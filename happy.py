from response import Response, Code, Status


class HappyService:
    BASE_PATH = '/happy'

    @staticmethod
    def validate_message(message: str) -> Response:
        return Response(
            code=Code.ok,
            status=Status.ok,
            data=message
        )
