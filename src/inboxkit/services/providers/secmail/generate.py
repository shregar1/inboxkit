from __future__ import annotations

from inboxkit.errors.provider.secmail import SecMailError
from inboxkit.models import TempInbox
from inboxkit.services.providers.secmail.abstraction import ISecMailGenerateService
from inboxkit.services.providers.secmail.inbox import SecMailInboxService
from inboxkit.utilities import HttpUtility


class SecMailGenerateService(ISecMailGenerateService):
    def list_domains(self) -> list[str]:
        data = HttpUtility.json("GET", f"{self.BASE}?action=getDomainList")
        if not isinstance(data, list):
            raise SecMailError(f"1secmail: bad domain list: {data}")
        return [str(x) for x in data]

    def gen_random_mailbox(self, count: int = 1) -> list[str]:
        n = max(1, min(int(count), 500))
        data = HttpUtility.json("GET", f"{self.BASE}?action=genRandomMailbox&count={n}")
        if not isinstance(data, list) or not data:
            raise SecMailError(f"1secmail: bad response: {data}")
        return [str(x).strip() for x in data]

    def mint(self) -> TempInbox:
        addresses = self.gen_random_mailbox(1)
        address = addresses[0]
        if "@" not in address:
            raise SecMailError(f"1secmail: bad address: {address}")
        login, domain = address.split("@", 1)
        inbox_svc = SecMailInboxService()
        return TempInbox(
            address=address,
            provider=self.PROVIDER,
            token=f"{login}@{domain}",
            meta={"login": login, "domain": domain},
            _list=inbox_svc.list_messages,
            _read=inbox_svc.read_message,
        )
