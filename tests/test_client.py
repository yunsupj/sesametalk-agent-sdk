import unittest
from uuid import uuid4
from sesametalk_agent_sdk import SesameTalkClient
from sesametalk_agent_sdk.client import _NoRedirect


class ClientTests(unittest.TestCase):
    def setUp(self):
        self.calls = []
        def fake(method, path, body, token):
            self.calls.append((method, path, body, token))
            return {"ok": True}
        self.client = SesameTalkClient("https://staging.example.invalid", transport=fake)
        self.agent = str(uuid4())
        self.credential = str(uuid4())

    def test_human_first_registration_and_claim(self):
        self.client.register_agent(human_jwt="human")
        self.client.claim_agent(self.agent, "claim", human_jwt="human")
        self.assertEqual(self.calls[0], ("POST", "/agent/v1/agents", {}, "human"))
        self.assertEqual(self.calls[1], ("POST", f"/agent/v1/agents/{self.agent}/claim", {"token": "claim"}, "human"))

    def test_agent_read_only_profile(self):
        self.client.agent_self(agent_token="agent")
        self.assertEqual(self.calls[0], ("GET", "/agent/v1/self", None, "agent"))

    def test_no_credential_in_public_profile(self):
        self.client.public_profile(self.agent)
        self.assertIsNone(self.calls[0][3])

    def test_revoke_and_suspend_are_owner_actions(self):
        self.client.revoke_agent_token(self.agent, self.credential, human_jwt="human")
        self.client.suspend_agent(self.agent, human_jwt="human")
        self.assertTrue(all(c[-1] == "human" for c in self.calls))

    def test_invalid_uuid_fails_before_transport(self):
        with self.assertRaises(ValueError):
            self.client.public_profile("not-uuid")
        self.assertEqual(self.calls, [])

    def test_redirects_disabled_for_secret_bearing_requests(self):
        self.assertIsNone(_NoRedirect().redirect_request(None, None, 307, "redirect", {}, "https://evil.example"))

    def test_disallow_non_https(self):
        with self.assertRaises(ValueError):
            SesameTalkClient("http://untrusted.example")


if __name__ == "__main__": unittest.main()
