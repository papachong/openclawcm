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
		# Handle OpenClaw's providers format: {providers: {glmcode: {baseUrl, models: [{id, name}]}}}
		providers_section = models_section.get("providers")
		if isinstance(providers_section, dict):
			for provider_key, provider_val in providers_section.items():
				if not isinstance(provider_val, dict):
					continue
				base_url = provider_val.get("baseUrl") or provider_val.get("base_url")
				api_type = provider_val.get("api") or provider_val.get("type") or "openai"
				# Extract models from provider's models array
				provider_models = provider_val.get("models") or []
				if isinstance(provider_models, list):
					for model_item in provider_models:
						if not isinstance(model_item, dict):
							continue
						model_id = model_item.get("id") or model_item.get("name")
						model_name = model_item.get("name") or model_id
						if not model_id:
							continue
						result.append({
							"name": f"{provider_key}/{model_id}",
							"model_name": model_id,
							"provider": provider_key,
							"base_url": base_url,
							"description": f"{model_name} ({api_type})",
						})

		# Fallback: handle direct key-value format
		if not result:
			for key, val in models_section.items():
				if key in ("mode", "providers"):
					continue
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
	"""Extract plugin/tool info from remote config payload.

	Handles OpenClaw's plugins format:
	{
		"plugins": {
			"entries": { "feishu": { "enabled": true }, ... },
			"installs": { "feishu": { "version": "1.0.0", ... }, ... }
		}
	}
	"""
	result: List[Dict[str, Optional[str]]] = []
	plugins = config.get("plugins") or config.get("tools") or config.get("skills") or {}

	if isinstance(plugins, dict):
		# Handle OpenClaw's entries/installs format
		entries = plugins.get("entries")
		installs = plugins.get("installs")

		if isinstance(entries, dict) or isinstance(installs, dict):
			# Merge entries and installs
			all_names = set()
			if isinstance(entries, dict):
				all_names.update(entries.keys())
			if isinstance(installs, dict):
				all_names.update(installs.keys())

			for name in all_names:
				entry_val = entries.get(name, {}) if isinstance(entries, dict) else {}
				install_val = installs.get(name, {}) if isinstance(installs, dict) else {}

				enabled = True
				if isinstance(entry_val, dict):
					enabled = entry_val.get("enabled", True)
				elif isinstance(entry_val, bool):
					enabled = entry_val

				version = "1.0.0"
				description = None
				if isinstance(install_val, dict):
					version = install_val.get("version") or "1.0.0"
					description = install_val.get("description")

				result.append({
					"name": name,
					"version": version,
					"description": description,
					"status": "installed" if enabled else "available",
				})
			return result

		# Fallback: handle direct key-value format
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


async def get_remote_skills(instance_url: str, token: str, agent_id: Optional[str] = None) -> List[Dict[str, Any]]:
	"""Fetch skills status from remote gateway via skills.status."""
	try:
		params = {}
		if agent_id:
			params["agentId"] = agent_id
		payload = await _gateway_call(instance_url, token, "skills.status", params)
		if isinstance(payload, dict):
			skills_list = payload.get("skills", [])
			if isinstance(skills_list, list):
				return skills_list
		return []
	except Exception:
		return []


async def get_remote_sessions(instance_url: str, token: str) -> List[Dict[str, Any]]:
	"""Fetch sessions list from remote gateway via sessions.list."""
	try:
		payload = await _gateway_call(instance_url, token, "sessions.list", {})
		if isinstance(payload, dict):
			sessions = payload.get("sessions", [])
			if isinstance(sessions, list):
				return sessions
		elif isinstance(payload, list):
			return payload
		return []
	except Exception:
		return []


async def send_agent_message(instance_url: str, token: str, message: str, session_key: Optional[str] = None) -> Dict[str, Any]:
	"""Send a message to an agent via gateway."""
	try:
		params = {"message": message}
		if session_key:
			params["sessionKey"] = session_key
		payload = await _gateway_call(instance_url, token, "agent", params)
		return payload if isinstance(payload, dict) else {}
	except Exception as e:
		return {"error": str(e)}


def _normalize_skills(skills_list: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
	"""Normalize skills from skills.status response."""
	result: List[Dict[str, Any]] = []
	for skill in skills_list:
		if not isinstance(skill, dict):
			continue
		name = skill.get("name")
		if not name:
			continue
		result.append({
			"name": name,
			"description": skill.get("description"),
			"source": skill.get("source", "unknown"),
			"bundled": skill.get("bundled", False),
			"file_path": skill.get("filePath"),
			"base_dir": skill.get("baseDir"),
			"skill_key": skill.get("skillKey") or name,
			"primary_env": skill.get("primaryEnv"),
			"emoji": skill.get("emoji"),
			"homepage": skill.get("homepage"),
			"always": skill.get("always", False),
			"disabled": skill.get("disabled", False),
			"eligible": skill.get("eligible", True),
			"version": "1.0.0",  # Skills don't have version in status
			"status": "installed" if skill.get("eligible", True) else "unavailable",
		})
	return result


async def sync_instance_config(instance_url: str, token: str) -> Dict[str, Any]:
	"""Sync full configuration from a remote OpenClaw instance.

	Returns a dict with keys: agents, models, plugins, skills, raw_config, gateway_version.
	"""
	result: Dict[str, Any] = {
		"agents": [],
		"models": [],
		"plugins": [],
		"skills": [],
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
		# The actual config might be nested under 'config' key (OpenClaw gateway format)
		actual_config = config
		if isinstance(config, dict) and "config" in config:
			actual_config = config.get("config", {})
		if isinstance(actual_config, dict):
			result["raw_config"] = actual_config
			result["models"] = _normalize_models(actual_config)
			result["plugins"] = _normalize_plugins(actual_config)
			# Extract gateway version if present
			gw = actual_config.get("gateway") or {}
			if isinstance(gw, dict):
				result["gateway_version"] = gw.get("version")
	except Exception as e:
		result["errors"].append(f"config.get: {str(e)}")

	# 3. Fetch actual skills from skills.status API
	try:
		skills_payload = await _gateway_call(instance_url, token, "skills.status", {})
		if isinstance(skills_payload, dict):
			skills_list = skills_payload.get("skills", [])
			if isinstance(skills_list, list):
				result["skills"] = _normalize_skills(skills_list)
	except Exception as e:
		result["errors"].append(f"skills.status: {str(e)}")

	return result
