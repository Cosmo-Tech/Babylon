from json import dumps, loads
from logging import getLogger

from click import echo, style

from Babylon.commands.api.datasets.services.datasets_api_svc import DatasetService
from Babylon.utils.credentials import get_keycloak_token
from Babylon.utils.environment import Environment
from Babylon.utils.response import CommandResponse

logger = getLogger(__name__)
env = Environment()


def deploy_dataset(file_content: str) -> dict:
    _ret = [""]
    _ret.append("Dadaset deployment")
    _ret.append("")
    echo(style("\n".join(_ret), bold=True, fg="green"))
    state = env.retrieve_state_func()
    api_section = state["services"]["api"]
    content = env.fill_template(data=file_content, state=state)
    keycloak_token, config = get_keycloak_token()
    payload: dict = content.get("spec").get("payload", {})
    spec = dict()
    spec["payload"] = dumps(payload, indent=2, ensure_ascii=True)
    payload_string = loads(spec["payload"])
    filename_array = [x["sourceName"] for x in payload_string["parts"]]
    dataset_service = DatasetService(keycloak_token=keycloak_token, spec=spec, config=config, state=api_section)
    if not payload.get("id"):
        logger.info("Creating Dataset")
        response = dataset_service.create(filename_array)
        if response is None:
            return CommandResponse.fail()
        dataset = response.json()
        logger.info(f"Runner {[dataset['id']]} successfully created")
    return dataset.get("id")
