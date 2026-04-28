from langchain.tools import tool

@tool
def multiply(first_int: int, second_int: int) -> int:
    """将两个整数相乘。用于需要精确整数乘法时。"""
    return first_int * second_int


@tool
def get_current_time() -> str:
    """返回当前本地日期与时间（ISO 格式）。用于回答现在几点、今天日期等问题。"""
    from datetime import datetime

    return datetime.now().isoformat(timespec="seconds")

@tool
def get_weather_for_location(city: str) -> str:
    """获取指定城市的天气。"""
    return f"{city}总是阳光明媚！"

def search_web(query: str) -> str:
    """在线搜索网络信息 用于回答用户的问题"""
    return "调用网络搜索功能"