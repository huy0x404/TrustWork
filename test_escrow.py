"""
Unit test suite and mock runner for TrustWork FreelanceEscrow Intelligent Contract.
Mocks the GenLayer VM runtime primitives to verify all contract methods and edge cases.
"""

import json
import unittest


# --- Mock GenLayer Runtime ---
class Address:
    def __init__(self, val):
        if isinstance(val, Address):
            self.val = val.val
        else:
            self.val = str(val).lower()

    @property
    def as_hex(self):
        return self.val

    def __eq__(self, other):
        if isinstance(other, Address):
            return self.val == other.val
        return self.val == str(other).lower()

    def __repr__(self):
        return f"Address('{self.val}')"


class u256(int):
    pass


class TreeMap(dict):
    def __class_getitem__(cls, item):
        return cls


class Message:
    def __init__(self):
        self.sender_address = Address("0xclient111111111111111111111111111111111111")


class NondetWeb:
    def render(self, url: str, mode: str = "text") -> str:
        if "partial" in url.lower():
            return "<html><body><h1>Project Title</h1><p>UI completed. Backend pending.</p></body></html>"
        elif "empty" in url.lower() or "404" in url.lower():
            return "<html><body>404 Not Found</body></html>"
        else:
            return "<html><body><h1>Complete SaaS App</h1><p>Auth, Stripe, Dashboard all working.</p></body></html>"


class Nondet:
    def __init__(self):
        self.web = NondetWeb()

    def exec_prompt(self, prompt: str) -> str:
        if "UI completed. Backend pending" in prompt:
            return json.dumps({
                "freelancer_pct": 50,
                "reasoning": "The freelancer delivered frontend UI nicely, but backend is incomplete per brief."
            })
        elif "404 Not Found" in prompt:
            return json.dumps({
                "freelancer_pct": 0,
                "reasoning": "The deliverable URL returns 404. None of the requirements were satisfied."
            })
        else:
            return json.dumps({
                "freelancer_pct": 100,
                "reasoning": "The deliverable meets all criteria specified in the agreed project brief."
            })


class EqPrinciple:
    def prompt_non_comparative(self, judge_fn, task: str, criteria: str) -> str:
        return judge_fn()


class PublicDecorators:
    @staticmethod
    def write(fn):
        return fn

    @staticmethod
    def view(fn):
        return fn


class StorageNamespace:
    def __init__(self):
        self.TreeMap = TreeMap


class ContractNamespace:
    class Contract:
        def __init_subclass__(cls):
            pass


class VMNamespace:
    class UserError(Exception):
        pass


class MockGL:
    def __init__(self):
        self.message = Message()
        self.nondet = Nondet()
        self.eq_principle = EqPrinciple()
        self.public = PublicDecorators()
        self.storage = StorageNamespace()
        self.contract = ContractNamespace()
        self.vm = VMNamespace()


gl = MockGL()

# Inject mocks into module namespace
import sys
import types

mock_module = types.ModuleType("genlayer")
mock_module.gl = gl
mock_module.public = gl.public
mock_module.storage = gl.storage
mock_module.contract = gl.contract
mock_module.nondet = gl.nondet
mock_module.eq_principle = gl.eq_principle
mock_module.message = gl.message
mock_module.vm = gl.vm

mock_module.Address = Address
mock_module.u256 = u256
mock_module.TreeMap = TreeMap

mock_module.types = types.ModuleType("genlayer.types")
mock_module.types.Address = Address
mock_module.types.u256 = u256

sys.modules["genlayer"] = mock_module
sys.modules["genlayer.types"] = mock_module.types
sys.modules["genlayer.storage"] = mock_module.storage
sys.modules["genlayer.contract"] = mock_module.contract

from freelance_escrow import FreelanceEscrow


class TestTrustWorkEscrow(unittest.TestCase):
    def setUp(self):
        self.escrow = FreelanceEscrow()
        self.escrow.jobs = {}
        self.client_addr = Address("0xclient111111111111111111111111111111111111")
        self.freelancer_addr = Address("0xfreelancer22222222222222222222222222222222")
        self.other_addr = Address("0xstranger33333333333333333333333333333333")
        gl.message.sender_address = self.client_addr

    def test_create_job(self):
        jid = self.escrow.create_job(
            freelancer=str(self.freelancer_addr.as_hex),
            brief="Build landing page",
            amount=500
        )
        self.assertEqual(jid, 1)
        self.assertEqual(self.escrow.job_count(), 1)

        job = self.escrow.get_job(1)
        self.assertEqual(job["id"], 1)
        self.assertEqual(job["status"], "OPEN")
        self.assertEqual(job["amount"], 500)
        self.assertEqual(job["brief"], "Build landing page")
        self.assertEqual(job["client"], self.client_addr.as_hex)
        self.assertEqual(job["freelancer"], self.freelancer_addr.as_hex)

    def test_cancel_job(self):
        jid = self.escrow.create_job(
            freelancer=str(self.freelancer_addr.as_hex),
            brief="Task that gets cancelled",
            amount=200
        )
        gl.message.sender_address = self.freelancer_addr
        with self.assertRaises(Exception):
            self.escrow.cancel_job(jid)

        gl.message.sender_address = self.client_addr
        self.escrow.cancel_job(jid)
        job = self.escrow.get_job(jid)
        self.assertEqual(job["status"], "REFUNDED")
        self.assertEqual(job["freelancer_pct"], 0)

    def test_happy_path_deliver_and_approve(self):
        jid = self.escrow.create_job(
            freelancer=str(self.freelancer_addr.as_hex),
            brief="Landing page with pricing table",
            amount=300
        )

        gl.message.sender_address = self.freelancer_addr
        self.escrow.submit_delivery(jid, "https://example.com/demo")
        job = self.escrow.get_job(jid)
        self.assertEqual(job["status"], "DELIVERED")
        self.assertEqual(job["deliverable_url"], "https://example.com/demo")

        gl.message.sender_address = self.client_addr
        self.escrow.approve(jid)
        job = self.escrow.get_job(jid)
        self.assertEqual(job["status"], "RELEASED")
        self.assertEqual(job["freelancer_pct"], 100)

    def test_dispute_and_ai_resolve_partial_split(self):
        jid = self.escrow.create_job(
            freelancer=str(self.freelancer_addr.as_hex),
            brief="Full SaaS app with auth & stripe integration",
            amount=1000
        )

        gl.message.sender_address = self.freelancer_addr
        self.escrow.submit_delivery(jid, "https://example.com/partial-work")

        gl.message.sender_address = self.client_addr
        self.escrow.open_dispute(jid, "Only UI is done. Stripe payment gateway is missing.")

        gl.message.sender_address = self.freelancer_addr
        self.escrow.respond_to_dispute(jid, "I spent 30 hours on the UI and design system.")

        gl.message.sender_address = self.other_addr
        self.escrow.resolve(jid)

        job = self.escrow.get_job(jid)
        self.assertEqual(job["status"], "SPLIT")
        self.assertEqual(job["freelancer_pct"], 50)
        self.assertIn("frontend UI nicely", job["reasoning"])

    def test_dispute_and_ai_resolve_zero_refund(self):
        jid = self.escrow.create_job(
            freelancer=str(self.freelancer_addr.as_hex),
            brief="Web3 Smart Contract",
            amount=800
        )

        gl.message.sender_address = self.freelancer_addr
        self.escrow.submit_delivery(jid, "https://example.com/404-link")

        gl.message.sender_address = self.client_addr
        self.escrow.open_dispute(jid, "Link is broken, 404 not found")

        gl.message.sender_address = self.other_addr
        self.escrow.resolve(jid)

        job = self.escrow.get_job(jid)
        self.assertEqual(job["status"], "REFUNDED")
        self.assertEqual(job["freelancer_pct"], 0)
        self.assertIn("404", job["reasoning"])


if __name__ == "__main__":
    unittest.main()
