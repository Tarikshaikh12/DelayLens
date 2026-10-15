"""Pure ASGI body limit; no private Request attributes and no consumed-body loss."""
from starlette.responses import JSONResponse

class BodyLimitMiddleware:
    def __init__(self,app,limit=1_000_000): self.app,self.limit=app,limit
    async def __call__(self,scope,receive,send):
        if scope['type']!='http' or scope['method']!='POST':
            return await self.app(scope,receive,send)
        # Buffer bounded bytes before invoking handlers; applies with or without Content-Length.
        messages=[];size=0
        while True:
            message=await receive()
            if message['type']=='http.disconnect': return
            size+=len(message.get('body',b''))
            if size>self.limit:
                return await JSONResponse({'detail':'Request exceeds 1 MB.'},status_code=413)(scope,receive,send)
            messages.append(message)
            if not message.get('more_body',False):break
        index=0
        async def replay():
            nonlocal index
            if index<len(messages):
                message=messages[index];index+=1;return message
            return await receive()
        await self.app(scope,replay,send)
