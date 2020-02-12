"""
A module that presents a data service (REST API) for interacting with the bond
registry.

Available functions:
- get_bonds: Return all bonds in the registry that match the search criteria.
- get_bond: Return a specific bond.
- create_bond: Create a bond.
- update_bond: Update a bond.
- delete_bond: Delete a bond.
- add_subscriber: Add a subscriber to a bond.
- remove_subscriber: Remove a subscriber from a bond.
"""
from fastapi import FastAPI, HTTPException
from registry import crud
from registry import logger
from registry.models import Bond, Subscriber
from registry.db import ConditionalCheckError, RegistryClientError

app = FastAPI()


@app.get("/bonds")
def get_bonds(cost_center_id: str = None,
              account_id: str = None,
              by_host: bool = True):
    """Return all bonds in the registry that match the search criteria.

    Args:
        cost_center_id (str, Default=None): The cost center to filter on.
            Whether to search on host or subscriber cost center depends on the
            value of by_host (see below).  If only the cost center is provided,
            return all records for that cost center.
        account_id (str, Default=None): The account identifier to filter on.
            Whether to search on host or subscriber account id depends on the
            value of by_host (see below). If the account id is provided, return
            all records for that account id. The cost center value (if
            provided) is ignored as an account can only belong to a single
            cost center (there being a 1-N relationship between cost center
            and account).
        by_host (bool, Default=True): If by_host is true, filter on host cost
            center and/or account id; Otherwise, filter on subscriber cost
            center and/or account id.

    Returns:
        A list of bond objects or an empty list if none are found."""
    logger.info(f"Get bonds: cost_center_id={cost_center_id}, "
                f"account_id={account_id}, by_host={by_host}")
    try:
        if by_host:
            if account_id is not None:
                bonds = crud.get_bonds_by_host_account_id(account_id)
            else:
                bonds = crud.get_bonds_by_host_cost_center(cost_center_id)
        else:
            if account_id is not None:
                bonds = crud.get_bonds_by_sub_account_id(account_id)
            else:
                bonds = crud.get_bonds_by_sub_cost_center(cost_center_id)
    except RegistryClientError as err:
        raise HTTPException(status_code=500, detail=str(err))
    return bonds


@app.get("/bonds/{bond_id}", response_model=Bond)
def get_bond(bond_id: str) -> Bond:
    """Return a specific bond.

    Args:
        bond_id (str): The bond id of the bond to fetch.

    Raises:
        HTTPException(400) if the bond does not exist.

    Returns:
        The requested bond."""
    logger.info(f"Get bond: bond_id={bond_id}")
    try:
        bond: Bond = crud.get_bond(bond_id)
    except RegistryClientError as err:
        raise HTTPException(status_code=500, detail=str(err))
    if bond is None:
        raise HTTPException(status_code=400,
                            detail=f"Bond {bond_id} not found.")
    return bond


@app.post("/bonds/", response_model=Bond)
def create_bond(bond: Bond) -> Bond:
    """Create a new bond.

    Args:
        bond (Bond): The bond object to insert.

    Raises:
        HTTPException(400) if the bond already exists.

    Returns:
        The bond created."""
    logger.info(f"Create bond: bond={bond}")
    try:
        new_bond = crud.create_bond(bond)
    except ConditionalCheckError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except RegistryClientError as err:
        raise HTTPException(status_code=500, detail=str(err))
    return new_bond


@app.put("/bonds/{bond_id}", response_model=Bond)
def update_bond(bond_id: str, bond: Bond) -> Bond:
    """Update a bond. Only updates those fields that have changed.

    Args:
        bond_id (str): The bond id of the bond to update.
        bond (Bond): The bond object with updates.

    Raises:
        HTTPException(400) if the bond does not exist.

    Returns:
        The updated bond."""
    logger.info(f"Update bond: bond_id={bond_id}, bond={bond}")

    # find the existing bond and overwrite only the changed values
    try:
        stored_bond: Bond = crud.get_bond(bond_id)
        if stored_bond is None:
            raise HTTPException(status_code=400,
                                detail=f"Bond {bond_id} not found.")
        update_data = bond.dict(exclude_unset=True)
        updated_bond = stored_bond.copy(update=update_data)

        new_bond = crud.update_bond(updated_bond)
    except ConditionalCheckError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except RegistryClientError as err:
        raise HTTPException(status_code=500, detail=str(err))
    return new_bond


@app.delete("/bonds/{bond_id}")
def delete_bond(bond_id: str) -> None:
    """Delete a bond. Do nothing if the bond is not found.

    Args:
        bond_id (str): The bond id of the bond to delete."""
    logger.info(f"Delete bond: {bond_id}")
    try:
        crud.delete_bond(bond_id)
    except RegistryClientError as err:
        raise HTTPException(status_code=500, detail=str(err))


@app.post("/bonds/{bond_id}/subscribers/", response_model=Bond)
def add_subscriber(bond_id: str, sub: Subscriber) -> Bond:
    """
    Add a subscriber to a bond. Overwrite subscriber details if the
    subscriber is already in the bond.

    Args:
        bond_id (str): The bond id of the bond to add the subscriber to.
        sub (Subscriber): The subscriber to add (or update).

    Raises:
         HTTPException(400) if the bond does not exist.

    Returns:
        The bond updated with the new subscriber."""
    logger.info(f"Add subscriber: bond_id={bond_id}, subscriber={sub}")
    try:
        bond = crud.add_subscriber(bond_id, sub)
    except ConditionalCheckError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except RegistryClientError as err:
        raise HTTPException(status_code=500, detail=str(err))
    return bond


@app.delete("/bonds/{bond_id}/subscribers/{sid}")
def remove_subscriber(bond_id: str, sid: str) -> Bond:
    """
    Remove a subscriber from a bond.

    Args:
        bond_id (str): The bond id of the bond to remove the subscriber from.
        sid (str): The subscriber identifier of the subscriber to be removed.

    Raises:
         HTTPException(400) if the bond does not exist.

    Returns:
        The bond updated minus the subscriber."""
    logger.info(f"Remove subscriber: bond_id={bond_id}, sid={sid}")
    try:
        bond = crud.remove_subscriber(bond_id, sid)
    except ConditionalCheckError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except RegistryClientError as err:
        raise HTTPException(status_code=500, detail=str(err))
    return bond
