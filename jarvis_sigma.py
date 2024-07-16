from response import Response, Code, Status


class JarvisSigmaService:
    BASE_PATH = '/jarvis_sigma'

    @staticmethod
    def process(message: str) -> Response:
        return Response(
            code=Code.ok,
            status=Status.ok,
            data=message
        )
