import pytest

from registry.models import Subscriber, Bond

"""
Bond and Subscriber mutation tests, e.g. adding and removing subscribers from
a bond.
"""


@pytest.fixture
def bond_no_subs():
    """Returns a Bond with no subscribers"""
    return Bond(bond_id='HostAcctA-SubAcctB',
                host_account_id='HostAcctA',
                sub_account_id='SubAcctB',
                host_cost_center='HostCostCenterA',
                sub_cost_center='SubCostCenterB')


@pytest.fixture
def bond_with_subs():
    """Return a Bond with an existing set of subscribers"""
    subs = {
            'eniesc200': Subscriber(sid='eniesc200',
                                    name='Ed',
                                    email='ed@mail.com'),
            'tfomoo100': Subscriber(sid='tfomoo100',
                                    name='Tom',
                                    email='tom@snail.com'),
            'bfoere300': Subscriber(sid='bfoere300',
                                    name='Bill',
                                    email='bill@mojo.com')
    }
    return Bond(bond_id='HostAcctA-SubAcctB',
                host_account_id='HostAcctA',
                sub_account_id='SubAcctB',
                host_cost_center='HostCostCenterA',
                sub_cost_center='SubCostCenterB',
                subscribers=subs)


def test_add_subscriber_no_subs(bond_no_subs):
    """Add a new subscriber to bond with no subs"""
    new_sub = Subscriber(sid='lmoreo200',
                         name='Lynne',
                         email='lynne@shlomo.com')
    bond_no_subs.add_subscriber(new_sub)
    assert len(bond_no_subs.subscribers) == 1
    assert new_sub.sid in bond_no_subs.subscribers.keys()


def test_add_subscriber_with_subs(bond_with_subs):
    """Add a new subscriber to a bond with subs"""
    new_sub = Subscriber(sid='lmoreo200',
                         name='Lynne',
                         email='lynne@shlomo.com')
    bond_with_subs.add_subscriber(new_sub)
    assert len(bond_with_subs.subscribers) == 4
    assert new_sub.sid in bond_with_subs.subscribers.keys()


def test_add_subscriber_as_dupe(bond_with_subs):
    """Attempt to add a new subscriber that already exists
    in the subscriber set
    """
    new_sub = Subscriber(sid='tfomoo100',
                         name='Tom',
                         email='tom@snail.com')
    bond_with_subs.add_subscriber(new_sub)
    assert len(bond_with_subs.subscribers) == 3   # nothing added
    assert new_sub.sid in bond_with_subs.subscribers.keys()  # still there


def test_add_subscriber_as_overwrite(bond_with_subs):
    """Attempt to update a subscriber"""
    new_sub = Subscriber(sid='tfomoo100',
                         name='Thomas',
                         email='tommy@snail.com')
    bond_with_subs.add_subscriber(new_sub)
    assert len(bond_with_subs.subscribers) == 3  # nothing added
    assert new_sub.sid in bond_with_subs.subscribers.keys()  # still there
    curSub = bond_with_subs.subscribers.get(new_sub.sid)
    assert new_sub.sid == curSub.sid
    assert new_sub.name == curSub.name
    assert new_sub.email == curSub.email


def test_remove_subscriber_empty_no_subs(bond_no_subs):
    """Remove a subscriber from an empty list"""
    bond_no_subs.remove_subscriber('sub0')
    assert len(bond_no_subs.subscribers) == 0  # nothing changed


def test_remove_subscriber_with_subs(bond_with_subs):
    """Remove a subscriber that exists in the list"""
    bond_with_subs.remove_subscriber('tfomoo100')
    assert len(bond_with_subs.subscribers) == 2  # one less
    assert 'tfomoo100' not in bond_with_subs.subscribers.keys()  # ours is gone


def test_remove_subscriber_not_existing(bond_with_subs):
    """Remove a subscriber who is not actually in the list"""
    bond_with_subs.remove_subscriber('sub0')
    assert len(bond_with_subs.subscribers) == 3  # nothing changed
