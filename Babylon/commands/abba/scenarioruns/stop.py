from click import command

from Babylon.utils.decorators import timing_decorator

from Babylon.utils.response import CommandResponse


@command()
@timing_decorator
def stop() -> CommandResponse:
    print("stop")
    return CommandResponse.success()
