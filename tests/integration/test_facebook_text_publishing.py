
from unittest.mock import Mock
from urllib.parse import parse_qs

from socialflow.core.destination import PublishingDestination
from socialflow.modules.accounts.models.account import Account
from socialflow.modules.accounts.models.facebook_page_config import (
    FacebookPageConfig,
)
from socialflow.modules.accounts.services.facebook_credential_keys import (
    FacebookCredentialKeys,
)
from socialflow.modules.facebook.adapters.facebook_publisher import (
    FacebookPublisher,
)
from socialflow.modules.facebook.api.facebook_graph_client import (
    FacebookGraphClient,
)
from socialflow.modules.facebook.api.facebook_http_transport import (
    FacebookHttpResponse,
)
from socialflow.modules.facebook.api.facebook_publishing_service import (
    FacebookPublishingService,
)
from socialflow.modules.posts.models.language import Language
from socialflow.modules.posts.models.post import Post
from socialflow.modules.posts.models.publish_request import PublishRequest
from socialflow.modules.posts.services.publish_post import PublishPost
from socialflow.modules.posts.services.publisher_router import PublisherRouter
from socialflow.modules.facebook.api.facebook_api_error import (
    FacebookApiError,
)
from socialflow.modules.posts.services.error_classifier import (
    ErrorCategory,
)


def test_facebook_text_publishing_end_to_end() -> None:
    account = Account(
        name="Test Facebook Page",
        destination=PublishingDestination.FACEBOOK,
        facebook_config=FacebookPageConfig(
            page_id="123456789",
            page_name="Test Page",
        ),
    )

    message = "Publishing to Facebook through SocialFlow"
    token = "test-page-access-token"

    credential_store = Mock()
    credential_store.get.return_value = token

    transport = Mock()
    transport.post.return_value = FacebookHttpResponse(
        status_code=200,
        body=b'{"id":"123456789_987654321"}',
    )

    graph_client = FacebookGraphClient(
        api_version="v24.0",
        transport=transport,
    )
    publishing_service = FacebookPublishingService(
        client=graph_client,
    )

    router = PublisherRouter(
        publishers={},
        account_factories={
            PublishingDestination.FACEBOOK: (
                lambda selected_account: FacebookPublisher(
                    account=selected_account,
                    credential_store=credential_store,
                    publishing_service=publishing_service,
                )
            ),
        },
    )

    publish_post = PublishPost(
        publisher_router=router,
        publication_id_generator=Mock(),
    )

    request = PublishRequest(
        post=Post(
            text=message,
            language=Language.ENGLISH,
        ),
        accounts=(account,),
    )

    results = publish_post.execute(request)

    assert len(results) == 1
    assert results[0].account is account
    assert results[0].succeeded is True
    assert results[0].error is None

    credential_store.get.assert_called_once_with(
        FacebookCredentialKeys.page_access_token(account)
    )

    transport.post.assert_called_once()

    kwargs = transport.post.call_args.kwargs

    assert kwargs["url"] == (
        "https://graph.facebook.com/v24.0/123456789/feed"
    )
    assert kwargs["headers"]["Authorization"] == (
        f"Bearer {token}"
    )
    assert kwargs["headers"]["Accept"] == "application/json"
    assert kwargs["headers"]["Content-Type"] == (
        "application/x-www-form-urlencoded"
    )
    assert kwargs["timeout"] == 10.0

    assert parse_qs(
        kwargs["body"].decode("utf-8")
    ) == {"message": [message]}


def test_facebook_api_rejection_returns_failed_result() -> None:
    account = Account(
        name="Rejected Facebook Page",
        destination=PublishingDestination.FACEBOOK,
        facebook_config=FacebookPageConfig(
            page_id="123456789",
            page_name="Rejected Page",
        ),
    )

    credential_store = Mock()
    credential_store.get.return_value = "test-page-access-token"

    transport = Mock()
    transport.post.return_value = FacebookHttpResponse(
        status_code=400,
        body=(
            b'{"error":{"message":"Invalid OAuth access token.",'
            b'"type":"OAuthException","code":190}}'
        ),
    )

    graph_client = FacebookGraphClient(
        api_version="v24.0",
        transport=transport,
    )
    publishing_service = FacebookPublishingService(
        client=graph_client,
    )

    router = PublisherRouter(
        publishers={},
        account_factories={
            PublishingDestination.FACEBOOK: (
                lambda selected_account: FacebookPublisher(
                    account=selected_account,
                    credential_store=credential_store,
                    publishing_service=publishing_service,
                )
            ),
        },
    )

    publish_post = PublishPost(
        publisher_router=router,
        publication_id_generator=Mock(),
    )

    request = PublishRequest(
        post=Post(
            text="Facebook rejection integration test",
            language=Language.ENGLISH,
        ),
        accounts=(account,),
    )

    results = publish_post.execute(request)

    assert len(results) == 1

    result = results[0]

    assert result.account is account
    assert result.succeeded is False
    assert isinstance(result.error, FacebookApiError)
    assert result.error_category is ErrorCategory.PERMANENT

    transport.post.assert_called_once()
    credential_store.get.assert_called_once_with(
        FacebookCredentialKeys.page_access_token(account)
    )


def test_facebook_transient_api_failure_returns_transient_result() -> None:
    account = Account(
        name="Temporary Failure Facebook Page",
        destination=PublishingDestination.FACEBOOK,
        facebook_config=FacebookPageConfig(
            page_id="123456789",
            page_name="Temporary Failure Page",
        ),
    )

    credential_store = Mock()
    credential_store.get.return_value = "test-page-access-token"

    transport = Mock()
    transport.post.return_value = FacebookHttpResponse(
        status_code=503,
        body=(
            b'{"error":{"message":"Service temporarily unavailable.",'
            b'"type":"ServerException","code":2}}'
        ),
    )

    graph_client = FacebookGraphClient(
        api_version="v24.0",
        transport=transport,
    )
    publishing_service = FacebookPublishingService(
        client=graph_client,
    )

    router = PublisherRouter(
        publishers={},
        account_factories={
            PublishingDestination.FACEBOOK: (
                lambda selected_account: FacebookPublisher(
                    account=selected_account,
                    credential_store=credential_store,
                    publishing_service=publishing_service,
                )
            ),
        },
    )

    publish_post = PublishPost(
        publisher_router=router,
        publication_id_generator=Mock(),
    )

    request = PublishRequest(
        post=Post(
            text="Facebook transient failure integration test",
            language=Language.ENGLISH,
        ),
        accounts=(account,),
    )

    results = publish_post.execute(request)

    assert len(results) == 1

    result = results[0]

    assert result.account is account
    assert result.succeeded is False
    assert isinstance(result.error, FacebookApiError)
    assert result.error.status_code == 503
    assert result.error.is_transient is True
    assert result.error_category is ErrorCategory.TRANSIENT

    transport.post.assert_called_once()
    credential_store.get.assert_called_once_with(
        FacebookCredentialKeys.page_access_token(account)
    )
