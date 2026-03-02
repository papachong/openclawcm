import asyncio
import json
import uuid
from typing import Any, Dict, List, Optional
from urllib.parse import urlparse

import websockets


def _to_ws_url(instance_url: str) -> str:
	parsed = urlparse(instance_url)
	scheme = parsed.scheme.lower()
	if scheme in {"ws", "wss"}:
		return instance_url.rstrip("/")
	if scheme == "https":
		return instance_url.replace("https://", "wss://", 1).rstrip("/")
	if scheme == "http":
		return instance_url.replace("http://", "ws://", 1).rstrip("/")
	return f"ws://{instance_url}".rstrip("/")


def _to_origin(instance_url: str) -> str:
	parsed = urlparse(instance_url)
	scheme = parsed.scheme.lower()
	if scheme in {"http", "https"}:
		return instance_url.rstrip("/")
	if scheme == "wss":
		return instance_url.replace("wss://", "https://", 1).rstrip("/")
	if scheme == "ws":
		return instance_url.replace("ws://", "http://", 1).rstrip("/")
	return f"http://{instance_url}".rstrip("/")


async def _gateway_call(instance_url: str, token: str, method: str, params: dict[str, Any]) -> Any:
	ws_url = _to_ws_url(instance_url)
	origin = _to_origin(instance_url)

	async with websockets.connect(
		ws_url,
		origin=origin,
		ping_interval=None,
		open_timeout=8,
		close_timeout=3,
	) as ws:
		connect_id = str(uuid.uuid4())
		connect_req = {
			"type": "req",
			"id": connect_id,
			"method": "connect",
			"params": {
				"minProtocol": 3,
				"maxProtocol": 3,
				"client": {
					"id": "gateway-client",
					"version": "openclawcm",
					"platform": "python",
					"mode": "backend",
				},
				"role": "operator",
				"scopes": ["operator.read", "operator.admin", "operator.approvals", "operator.pairing"],
				"caps": [],
				"auth": {"token": token},
				"locale": "zh-CN",
			},
		}
		await ws.send(json.dumps(connect_req, ensure_ascii=False))

		while True:
			raw = await asyncio.wait_for(ws.recv(), timeout=8)
			msg = json.loads(raw)
			if msg.get("type") == "res" and msg.get("id") == connect_id:
				if not msg.get("ok"):
					err = msg.get("error") or {}
					raise RuntimeError(err.get("message") or "gateway connect failed")
				break

		req_id = str(uuid.uuid4())
		req = {"type": "req", "id": req_id, "method": method, "params": params}
		await ws.send(json.dumps(req, ensure_ascii=False))

		while True:
			raw = await asyncio.wait_for(ws.recv(), timeout=8)
			msg = json.loads(raw)
			if msg.get("type") == "res" and msg.get("id") == req_id:
				if not msg.get("ok"):
					err = msg.get("error") or {}
					raise RuntimeError(err.get("message") or f"{method} failed")
				return msg.get("payload")


def _normalize_agents(payload: Any) -> List[Dict[str, Optional[str]]]:
	if isinstance(payload, dict):
		raw_agents = payload.get("agents")
	elif isinstance(payload, list):
		raw_agents = payload
	else:
		raw_agents = []

	result: List[Dict[str, Optional[str]]] = []
	for item in raw_agents or []:
		if not isinstance(item, dict):
			continue
		name = item.get("name") or item.get("id") or item.get("agentId")
		if not name:
			continue
		role = item.get("role") or item.get("title")
		slug = item.get("slug") or item.get("id")
		version = item.get("version")
		permission = item.get("permission") or item.get("permissions")
		desc_parts = []
		if slug:
			desc_parts.append(f"slug={slug}")
		if version:
			desc_parts.append(f"version={version}")
		if permission:
			desc_parts.append(f"permission={permission}")
		result.append({
			"name": str(name),
			"role": str(role) if role else None,
			"description": " | ".join(desc_parts) if desc_parts else None,
		})
	return result


async def list_remote_agents(instance_url: str, token: str) -> List[Dict[str, Optional[str]]]:
	payload = await _gateway_call(instance_url, token, "agents.list", {})
	return _normalize_agents(payload)


async def get_remote_config(instance_url: str, token: str) -> Dict[str, Any]:
	"""Fetch full config from remote gateway via config.get."""
	try:
		payload = await _gateway_call(instance_url, token, "config.get", {})
		return payload if isinstance(payload, dict) else {}
	except Exception:
		return {}


def _normalize_models(config: Dict[str, Any]) -> List[Dict[str, Optional[str]]]:
	"""Extract model provider/config info from remote config payload."""
	result: List[Dict[str, Optional[str]]] = []
	models_section = config.get("models") or config.get("model") or {}
	if isinstance(models_section, dict):
		for key, val in models_section.items():
			if isinstance(val, dict):
				result.append({
					"name": val.get("name") or key,
					"model_name": val.get("model") or val.get("modelName") or val.get("model_name") or key,
					"provider": val.get("provider") or val.get("type") or "unknown",
					"base_url": val.get("baseUrl") or val.get("base_url") or val.get("endpoint") or None,
					"description": val.get("description") or None,
				})
			elif isinstance(val, str):
				result.append({"name": key, "model_name": val, "provider": "unknown", "base_url": None, "description": None})
	# Also try flat model list
	model_list = config.get("modelList") or config.get("model_list") or []
	if isinstance(model_list, list):
		for item in model_list:
			if isinstance(item, dict):
				result.append({
					"name": item.get("name") or item.get("id") or "unknown",
					"model_name": item.get("model") or item.get("modelName") or item.get("name") or "unknown",
					"provider": item.get("provider") or item.get("type") or "unknown",
					"base_url": item.get("baseUrl") or item.get("base_url") or None,
					"description": item.get("description") or None,
				})
	return result


def _normalize_plugins(config: Dict[str, Any]) -> List[Dict[str, Optional[str]]]:
	"""Extract plugin/tool info from remote config payload."""
	result: List[Dict[str, Optional[str]]] = []
	plugins = config.get("plugins") or config.get("tools") or config.get("skills") or {}
	if isinstance(plugins, dict):
		for key, val in plugins.items():
			if isinstance(val, dict):
				result.append({
					"name": val.get("name") or key,
					"version": val.get("version") or "1.0.0",
					"description": val.get("description") or None,
					"status": "installed" if val.get("enabled", True) else "available",
				})
			elif isinstance(val, (str, bool)):
				result.append({"name": key, "version": "1.0.0", "description": None, "status": "installed"})
	elif isinstance(plugins, list):
		for item in plugins:
			if isinstance(item, dict):
				result.append({
					"name": item.get("name") or item.get("id") or "unknown",
					"version": item.get("version") or "1.0.0",
					"description": item.get("description") or None,
					"status": "installed" if item.get("enabled", True) else "available",
				})
			elif isinstance(item, str):
				result.append({"name": item, "version": "1.0.0", "description": None, "status": "installed"})
	return result


async def sync_instance_config(instance_url: str, token: str) -> Dict[str, Any]:
	"""Sync full configuration from a remote OpenClaw instance.

	Returns a dict with keys: agents, models, plugins, raw_config, gateway_version.
	"""
	result: Dict[str, Any] = {
		"agents": [],
		"models": [],
		"plugins": [],
		"raw_config": {},
		"gateway_version": None,
		"errors": [],
	}

	# 1. Fetch agents
	try:
		agents_payload = await _gateway_call(instance_url, token, "agents.list", {})
		result["agents"] = _normalize_agents(agents_payload)
	except Exception as e:
		result["errors"].append(f"agents.list: {str(e)}")

	# 2. Fetch config (models, plugins, etc.)
	try:
		config = await _gateway_call(instance_url, token, "config.get", {})
		if isinstance(config, dict):
			result["raw_config"] = config
			result["models"] = _normalize_models(config)
			result["plugins"] = _normalize_plugins(config)
			# Extract gateway version if present
			gw = config.get("gateway") or {}
			if isinstance(gw, dict):
				result["gateway_version"] = gw.get("version")
	except Exception as e:
		result["errors"].append(f"config.get: {str(e)}")

	return result
