import pytest

from Babylon.utils.environment import Environment


def test_init():
    """Testing Environment"""
    env = Environment()
    assert env.configuration
    assert env.working_dir


def test_datastore_store_valid_key():
    """Test if storing data with a valid key works"""
    env = Environment()
    env.reset_data_store()

    path = [
        'SimpleKey',
    ]
    value = "Value"

    assert env.store_data(path, value)


def test_datastore_store_valid_composite_key():
    """Test if storing data using a composite key works"""
    env = Environment()
    env.reset_data_store()

    path = ['Composite', 'Key']
    value = "Value"

    assert env.store_data(path, value)


def test_set_with_no_path_into_storage():
    """Test that a key is required to send data into storage"""
    env = Environment()
    env.reset_data_store()
    path = []
    value = "Value"

    with pytest.raises(KeyError):
        env.store_data(path, value)


def test_datastore_refuse_key_over_existing():
    """Test if storing data over already existing data is correctly blocked"""
    env = Environment()
    env.reset_data_store()
    path = ['Key']
    value = "Value"
    assert env.store_data(path, value)
    path = ['Key', 'Key2']
    value = "Value"

    with pytest.raises(KeyError):
        env.store_data(path, value)


def test_datastore_composite_keys_stores():
    """Test that sub-keys can be added"""
    env = Environment()
    env.reset_data_store()
    path = ['Key', 'Key1']
    value = "Value"
    assert env.store_data(path, value)
    path = ['Key', 'Key2']
    value = "Value"

    assert env.store_data(path, value)


def test_get_data_from_storage():
    """Test to get back data from storage"""
    env = Environment()
    env.reset_data_store()
    path = ['Key', 'Key1']
    value = "Value"
    assert env.store_data(path, value)

    assert env.get_data(path) == value


def test_get_non_existing_data_from_storage():
    """Test that non-existing key from storage does not return"""
    env = Environment()
    env.reset_data_store()
    path = ['Key', 'Key1']

    with pytest.raises(KeyError):
        env.get_data(path)


def test_get_with_no_path_from_storage():
    """Test that a key is required to get data from storage"""
    env = Environment()
    env.reset_data_store()
    path = []

    with pytest.raises(KeyError):
        env.get_data(path)
