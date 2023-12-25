from fastapi import HTTPException, Request, Response
from server.routes.auth import get_current_client


async def auth_middleware(request: Request, call_next):
    try:
        # 获取 token，可能需要根据实际情况调整获取方式
        token = request.headers.get('Authorization')
        if not token:
            raise HTTPException(401, 'UnAuthorized')
        if token.startswith("Bearer "):
            token = token[7:]  # 或者使用 split() 方法分割字符串
        # 调用认证逻辑
        client_id = await get_current_client(token)
    except HTTPException as e:
        # 如果认证失败，则返回错误响应
        return Response(content=e.detail, status_code=e.status_code)

    # 如果认证成功，继续处理请求
    response = await call_next(request)
    return response