from typing import Dict
from pydantic import BaseModel, EmailStr

from registry import logger


class Subscriber(BaseModel):
    """Represents a subscriber.

    Each bond maintains a list of subscribers. These are individuals who are
    affiliated with the subscriber account and are authorized, based on the
    bond, to request services from the host account.

    Public attributes:
    - sid (str): The subscriber unique identifier.
    - name (str): The name of the subscriber.
    - email (pydantic EmailStr): The email address of the subscriber.
    """
    sid: str
    name: str
    email: EmailStr


class Bond(BaseModel):
    """Represents a bond.

    A bond represents a relationship between two parties (accounts) whereby one
    party (the subscriber account) promises to pay the other (the host account)
    for services provided by the host. This is also known as a 'charge-back
    relationship'.

    The natural key for a bond is a composite of host account id and subscriber
    account id.

    A cost center represents a funding entity and is used to group accounts.
    There is a one-to-many relationship between cost centers and accounts. Host
    and subscriber accounts may belong to the same cost center.

    Public attributes:
    - bond_id (str): The bond unique identifier.
    - host_account_id (str): The identifier of the host account.
    - sub_account_id (str): The identifier of the subscriber account.
    - host_cost_center (str): The identifier of the host cost center.
    - sub_cost_center (str): The identifier of the subscriber cost center.
    - subscribers (dict): The collection of bond subscribers (dict - keyed on
        subscriber id (sid)).
    """
    bond_id: str
    host_account_id: str
    sub_account_id: str
    host_cost_center: str
    sub_cost_center: str
    subscribers: Dict[str, Subscriber] = {}

    def add_subscriber(self, sub: Subscriber) -> None:
        """Add a subscriber to the bond. Overwrite if the sub already exists.

        Args:
            sub (Subscriber): The subscriber object to add to the bond.
        """
        logger.info(f"Adding subscriber '{sub}' to '{self}'")
        self.subscribers[sub.sid] = sub

    def remove_subscriber(self, sub_id: str) -> None:
        """Remove a subscriber from the bond. Ignore if the
        bond does not contain that subscriber.

        Args:
            sub_id (str): The subscriber unique identifier.
        """
        logger.info(f"Removing subscriber with id '{sub_id}' from '{self}'")
        self.subscribers.pop(sub_id, None)  # ignores the KeyError if not found
