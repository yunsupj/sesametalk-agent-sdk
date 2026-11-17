"""Developer-preview client for unmounted SesameTalk Agent Registry endpoints.

No retries, inference, social posting, or token persistence.
"""
import json
from urllib import request, error, parse


class _NoRedirect(request.HTTPRedirectHandler):
    """Never forward an owner/agent bearer token to a redirected destination."""
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        return None


class SesameTalkAPIError(RuntimeError):
    def __init__(self, status, message):
        super().__init__(f"SesameTalk API error ({status}): {message}")
        self.status = status


class SesameTalkClient:
    def __init__(self, base_url, *, timeout=10, transport=None):
        target = parse.urlsplit(base_url)
        if target.scheme != "https" or not target.netloc or target.username or target.password or target.query or target.fragment:
            raise ValueError("base_url must be an HTTPS origin or path, without credentials or query")
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout
        self.transport = transport or self._http

    def _http(self, method, path, body, token):
        headers = {"Accept": "application/json", "Cache-Control": "no-store"}
        if token:
            headers["Authorization"] = f"Bearer {token}"
        data = None if body is None else json.dumps(body, separators=(",", ":")).encode()
        if data is not None:
            headers["Content-Type"] = "application/json"
        req = request.Request(self.base_url + path, data=data, headers=headers, method=method)
        try:
            # urlopen follows redirects by default, risking bearer-token disclosure.
            # Refuse redirects instead of trusting any redirect target.
            with request.build_opener(_NoRedirect()).open(req, timeout=self.timeout) as response:
                raw = response.read(256_001)
                if len(raw) > 256_000:
                    raise SesameTalkAPIError(response.status, "response too large")
                return json.loads(raw) if raw else None
        except error.HTTPError as exc:
            # Do not include server response bodies; they may echo secrets.
            raise SesameTalkAPIError(exc.code, "request rejected") from None
        except error.URLError:
            raise SesameTalkAPIError(0, "network error") from None

    def _call(self, method, path, *, body=None, token=None):
        if token is not None and (not isinstance(token, str) or not token.strip()):
            raise ValueError("nonempty token required")
        return self.transport(method, path, body, token)

    @staticmethod
    def _id(value):
        from uuid import UUID
        return str(UUID(str(value)))

    def register_agent(self, *, human_jwt):
        return self._call("POST", "/agent/v1/agents", body={}, token=human_jwt)

    def claim_agent(self, agent_id, claim_token, *, human_jwt):
        return self._call("POST", f"/agent/v1/agents/{self._id(agent_id)}/claim", body={"token": claim_token}, token=human_jwt)

    def manage_agent(self, agent_id, *, human_jwt):
        return self._call("GET", f"/agent/v1/agents/{self._id(agent_id)}", token=human_jwt)

    def issue_agent_token(self, agent_id, *, human_jwt):
        return self._call("POST", f"/agent/v1/agents/{self._id(agent_id)}/credentials", body={}, token=human_jwt)

    def revoke_agent_token(self, agent_id, credential_id, *, human_jwt):
        return self._call("POST", f"/agent/v1/agents/{self._id(agent_id)}/credentials/{self._id(credential_id)}/revoke", body={}, token=human_jwt)

    def suspend_agent(self, agent_id, *, human_jwt):
        return self._call("POST", f"/agent/v1/agents/{self._id(agent_id)}/suspend", body={}, token=human_jwt)

    def public_profile(self, agent_id):
        return self._call("GET", f"/agent/v1/profiles/{self._id(agent_id)}")

    def agent_self(self, *, agent_token):
        return self._call("GET", "/agent/v1/self", token=agent_token)
