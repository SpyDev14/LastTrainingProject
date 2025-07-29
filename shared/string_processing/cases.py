import re

def camel_to_snake_case(text: str) -> str:
	"""
	Преобразует `CamelCase` в `snake_case`<br>
	```
	"CamelCase" => "camel_case"
	"MyHTTPResponse" => "my_http_response"
	"Weird_CamelCase" => "weird_camel_case"
	```
	"""
	return re.sub(r"(?<=[a-z])(?=[A-Z])|(?<=[A-Z])(?=[A-Z][a-z])", '_', text).lower()
