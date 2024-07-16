from response import Response, Code, Status


class JarvisAlphaService:
    BASE_PATH = '/jarvis_alpha'

    @staticmethod
    def process(message: str) -> Response:
        return Response(
            code=Code.ok,
            status=Status.ok,
            data=message
        )
