def test_collect_module(handler) -> None:
    """Assert existing module can be collected."""
    identifier = "github.com/gin-gonic/gin"
    handler.collect(identifier) 
    assert handler._collected[identifier] is not None