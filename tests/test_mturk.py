import datetime
import mock
import os
import pytest
import socket
import time
from boto.resultset import ResultSet
from boto.mturk.price import Price
from boto.mturk.connection import Assignment
from boto.mturk.connection import HITTypeId
from boto.mturk.connection import HIT
from boto.mturk.connection import Qualification
from boto.mturk.connection import QualificationType
from boto.mturk.connection import MTurkConnection
from boto.mturk.connection import MTurkRequestError
from dallinger.mturk import DuplicateQualificationNameError
from dallinger.mturk import MTurkService
from dallinger.mturk import MTurkServiceException
from dallinger.mturk import QualificationNotFoundException
from dallinger.utils import generate_random_id


TEST_HIT_DESCRIPTION = '***TEST SUITE HIT***'
TEST_QUALIFICATION_DESCRIPTION = '***TEST SUITE QUALIFICATION***'


class FixtureConfigurationError(Exception):
    """To clarify that the error is with test configuration,
    not production code.
    """


def system_marker():
    return ':'.join(os.uname()).replace(' ', '')


def name_with_hostname_prefix():
    hostname = socket.gethostname()
    name = "{}:{}".format(hostname, generate_random_id(size=32))
    return name


def as_resultset(things):
    if not isinstance(things, (list, tuple)):
        things = [things]
    result = ResultSet()
    for thing in things:
        result.append(thing)
    return result


def fake_balance_response():
    return as_resultset(Price(1.00))


def fake_hit_type_response():
    return {
        u'HITTypeId': unicode(generate_random_id(size=32)),
        'ResponseMetadata': {
            'HTTPHeaders': {
                'content-length': '46',
                'content-type': 'application/x-amz-json-1.1',
                'date': 'Thu, 08 Feb 2018 23:37:18 GMT',
                'x-amzn-requestid': '009317a6-0d29-11e8-94f2-878e743a48be'
            },
            'HTTPStatusCode': 200,
            'RequestId': '009317a6-0d29-11e8-94f2-878e743a48be',
            'RetryAttempts': 0
        }
    }


def fake_hit_response(**kwargs):
    canned_response = {
        u'HIT': {
            u'AssignmentDurationInSeconds': 900,
            u'AutoApprovalDelayInSeconds': 0,
            u'CreationTime': datetime.datetime(2018, 1, 1, 1, 26, 52, 54000),
            u'Description': u'***TEST SUITE HIT***43683',
            u'Expiration': datetime.datetime(2018, 1, 1, 1, 27, 26, 54000),
            u'HITGroupId': u'36IAL8HYPYM1MDNBSTAEZW89WH74RJ',
            u'HITId': u'3X7837UUADRXYCA1K7JAJLKC66DJ60',
            u'HITReviewStatus': u'NotReviewed',
            u'HITStatus': u'Assignable',
            u'HITTypeId': u'3V76OXST9SAE3THKN85FUPK7730050',
            u'Keywords': u'testkw1,testkw2',
            u'MaxAssignments': 1,
            u'NumberOfAssignmentsAvailable': 1,
            u'NumberOfAssignmentsCompleted': 0,
            u'NumberOfAssignmentsPending': 0,
            u'QualificationRequirements': [
                {
                    u'Comparator': u'GreaterThanOrEqualTo',
                    u'IntegerValues': [95],
                    u'QualificationTypeId': u'000000000000000000L0',
                    u'RequiredToPreview': True
                },
                {
                    u'Comparator': u'EqualTo',
                    u'LocaleValues': [{u'Country': u'US'}],
                    u'QualificationTypeId': u'00000000000000000071',
                    u'RequiredToPreview': True
                }
            ],
            u'Question': u'<ExternalQuestion xmlns="http://mechanicalturk.amazonaws.com/AWSMechanicalTurkDataSchemas/2006-07-14/ExternalQuestion.xsd"><ExternalURL>https://url-of-ad-route</ExternalURL><FrameHeight>600</FrameHeight></ExternalQuestion>',
            u'Reward': u'0.01',
            u'Title': u'Test Title'
        },
        'ResponseMetadata': {
            'HTTPHeaders': {
                'content-length': '1075',
                'content-type': 'application/x-amz-json-1.1',
                'date': 'Wed, 07 Feb 2018 22:26:51 GMT',
                'x-amzn-requestid': 'fea8d1a0-0c55-11e8-aae4-030e1dad6670'
            },
            'HTTPStatusCode': 200,
            'RequestId': 'fea8d1a0-0c55-11e8-aae4-030e1dad6670',
            'RetryAttempts': 0
        }
    }
    return canned_response


def fake_qualification_response():
    canned_response = {
        u'Qualification': {
            u'GrantTime': datetime.datetime(2018, 2, 7, 17, 0, 48),
            u'IntegerValue': 2,
            u'QualificationTypeId': unicode(generate_random_id(size=32)),
            u'Status': u'Granted',
            u'WorkerId': u'FAKE_WORKER_ID'
        },
        'ResponseMetadata': {
            'HTTPHeaders': {
                'content-length': '164',
                'content-type': 'application/x-amz-json-1.1',
                'date': 'Thu, 08 Feb 2018 01:00:48 GMT',
                'x-amzn-requestid': '806337c8-0c6b-11e8-9668-91a85782438a'
            },
            'HTTPStatusCode': 200,
            'RequestId': '806337c8-0c6b-11e8-9668-91a85782438a',
            'RetryAttempts': 0
        }
    }

    return canned_response


def fake_qualification_type_response():
    canned_response = {
        u'QualificationType': {
            u'AutoGranted': False,
            u'CreationTime': datetime.datetime(2018, 1, 1, 12, 00, 00),
            u'Description': u'***TEST SUITE QUALIFICATION***',
            u'IsRequestable': True,
            u'Name': u'Test Qualifiction',
            u'QualificationTypeId': generate_random_id(size=32),
            u'QualificationTypeStatus': u'Active',
        }
    }
    return canned_response


def fake_list_qualification_types_response(qtypes=None):
    if qtypes is None:
        qtypes = [fake_qualification_type_response()['QualificationType']]

    canned_response = {
        u'NextToken': u'p1:X9LiQOsIM4deZdilfj5jYSg4V3yoreBuFB9P4GEWkiM60u/Gcr30+cnSqb5q',
        u'NumResults': 1,
        u'QualificationTypes': qtypes,
        'ResponseMetadata': {
            'HTTPHeaders': {
                'content-length': '384',
                'content-type': 'application/x-amz-json-1.1',
                'date': 'Thu, 08 Feb 2018 22:52:22 GMT',
                'x-amzn-requestid': 'b94c13ff-0d22-11e8-9668-91a85782438a'
            },
            'HTTPStatusCode': 200,
            'RequestId': 'b94c13ff-0d22-11e8-9668-91a85782438a',
            'RetryAttempts': 0
        }
    }

    return canned_response


def standard_hit_config(**kwargs):
    defaults = {
        'ad_url': 'https://url-of-ad-route',
        'approve_requirement': 95,
        'us_only': True,
        'lifetime_days': 0.0004,  # 34 seconds (30 is minimum)
        'max_assignments': 1,
        'notification_url': 'https://url-of-notification-route',
        'title': 'Test Title',
        'keywords': ['testkw1', 'testkw2'],
        'reward': .01,
        'duration_hours': .25
    }
    defaults.update(**kwargs)
    # Use fixed description, since this is how we clean up:
    defaults['description'] = TEST_HIT_DESCRIPTION + system_marker()

    return defaults


@pytest.fixture
def mturk(aws_creds):
    params = {'region_name': 'us-east-1'}
    params.update(aws_creds)
    service = MTurkService(**params)

    return service


@pytest.fixture
def with_cleanup(aws_creds, request):

    # tear-down: clean up all specially-marked HITs:
    def test_hits_only(hit):
        return TEST_HIT_DESCRIPTION in hit['description']
        return hit['description'] == TEST_HIT_DESCRIPTION + system_marker()

    # service = MTurkService(**aws_creds)
    params = {'region_name': 'us-east-1'}
    params.update(aws_creds)
    service = MTurkService(**params)

    # In tests we do a lot of querying of Qualifications we only just created,
    # so we need a long time-out
    service.max_wait_secs = 60.0
    try:
        yield service
    except Exception as e:
        raise e
    finally:
        try:
            for hit in service.get_hits(test_hits_only):
                service.disable_hit(hit['id'])
        except Exception:
            # Broad exception so we don't leak credentials in Travis CI logs
            pass


@pytest.fixture(scope="class")
def worker_id():
    # Get a worker ID from the environment or tests/config.py
    import os
    workerid = os.getenv('mturk_worker_id')
    if not workerid:
        try:
            from . import config
            workerid = config.mturk_worker_id
        except Exception:
            pass
    if not workerid:
        raise FixtureConfigurationError(
            'No "mturk_worker_id" value found. '
            'Either set this value or skip these tests with '
            '`pytest -m "not mturkworker"`'
        )
    return workerid


@pytest.fixture
def qtype(mturk):
    # build
    name = name_with_hostname_prefix()
    qtype = mturk.create_qualification_type(
        name=name,
        description=TEST_QUALIFICATION_DESCRIPTION,
        status='Active',
    )

    yield qtype

    # clean up
    mturk.dispose_qualification_type(qtype['id'])


@pytest.mark.mturk
@pytest.mark.mturkworker
class TestMTurkServiceIntegrationSmokeTest(object):
    """Hits about 75% of the MTurkService class with actual boto.mturk network
    calls. For comprehensive system tests, run with the --mturkfull option.
    """

    def test_create_hit_lifecycle(self, with_cleanup, qtype, worker_id):
        result = with_cleanup.get_qualification_type_by_name(qtype['name'])
        assert qtype == result

        with_cleanup.assign_qualification(qtype['id'], worker_id, score=2)

        workers = with_cleanup.get_workers_with_qualification(qtype['id'])

        assert worker_id in [w['id'] for w in workers]

        result = with_cleanup.increment_qualification_score(
            qtype['name'], worker_id)

        assert result['score'] == 3

        config = standard_hit_config(
            max_assignments=2,
            blacklist=[qtype['name']]
        )
        hit = with_cleanup.create_hit(**config)
        assert hit['status'] == 'Assignable'
        assert hit['max_assignments'] == 2

        # There is a lag before extension is possible
        sleep_secs = 2
        max_wait = 30
        time.sleep(sleep_secs)
        start = time.time()
        updated = None
        while not updated and time.time() - start < max_wait:
            try:
                updated = with_cleanup.extend_hit(
                    hit['id'], number=1, duration_hours=.25
                )
            except MTurkServiceException:
                time.sleep(sleep_secs)

        if updated is None:
            pytest.fail("HIT was never updated")
        else:
            assert updated['max_assignments'] == 3
        assert with_cleanup.disable_hit(hit['id'])


@pytest.mark.mturk
@pytest.mark.skipif(not pytest.config.getvalue("mturkfull"),
                    reason="--mturkfull was not specified")
class TestMTurkService(object):

    def loop_until_2_quals(self, mturk_helper, query):
        args = {
            'Query': query,
            'MustBeRequestable': False,
            'MustBeOwnedByCaller': True,
            'MaxResults': 2,
        }
        while len(mturk_helper.mturk.list_qualification_types(**args)['QualificationTypes']) < 2:
            time.sleep(1)
        return True

    def test_check_credentials_good_credentials(self, mturk):
        is_authenticated = mturk.check_credentials()
        assert is_authenticated

    def test_check_credentials_bad_credentials(self, mturk):
        mturk.aws_access_key_id = 'fake key id'
        mturk.aws_secret_access_key = 'fake secret'
        with pytest.raises(MTurkServiceException):
            mturk.check_credentials()

    def test_check_credentials_no_creds_set_raises(self, mturk):
        mturk.aws_access_key_id = ''
        mturk.aws_secret_access_key = ''
        with pytest.raises(MTurkServiceException):
            mturk.check_credentials()

    def test_register_hit_type(self, mturk):
        config = {
            'title': 'Test Title',
            'description': 'Test Description',
            'keywords': ['testkw1', 'testkw2'],
            'reward': .01,
            'duration_hours': .25,
            'qualifications': mturk.build_hit_qualifications(95, True, None)
        }
        hit_type_id = mturk.register_hit_type(**config)

        assert isinstance(hit_type_id, unicode)

    def test_register_notification_url(self, mturk):
        config = {
            'title': 'Test Title',
            'description': 'Test Description',
            'keywords': ['testkw1', 'testkw2'],
            'reward': .01,
            'duration_hours': .25,
            'qualifications': mturk.build_hit_qualifications(95, True, None)
        }
        url = 'https://url-of-notification-route'
        hit_type_id = mturk.register_hit_type(**config)

        assert mturk.set_rest_notification(url, hit_type_id) is True

    def test_create_hit(self, with_cleanup):
        hit = with_cleanup.create_hit(**standard_hit_config())
        assert hit['status'] == 'Assignable'
        assert hit['max_assignments'] == 1

    def test_create_hit_two_assignments(self, with_cleanup):
        hit = with_cleanup.create_hit(**standard_hit_config(max_assignments=2))
        assert hit['status'] == 'Assignable'
        assert hit['max_assignments'] == 2

    def test_create_hit_with_valid_blacklist(self, with_cleanup, qtype):
        hit = with_cleanup.create_hit(**standard_hit_config(blacklist=[qtype['name']]))
        assert hit['status'] == 'Assignable'

    def test_extend_hit_with_valid_hit_id(self, with_cleanup):
        hit = with_cleanup.create_hit(**standard_hit_config())
        time.sleep(15)  # Time lag before HIT is available for extension
        updated = with_cleanup.extend_hit(hit['id'], number=1, duration_hours=.25)

        assert updated['max_assignments'] == 2
        clock_skew = .01
        expected_extension = datetime.timedelta(hours=.25 - clock_skew)
        assert updated['expiration'] >= hit['expiration'] + expected_extension

    def test_extend_hit_with_invalid_hit_id_raises(self, mturk):
        with pytest.raises(MTurkServiceException):
            mturk.extend_hit('dud', number=1, duration_hours=.25)

    def test_disable_hit_with_valid_hit_id(self, with_cleanup):
        hit = with_cleanup.create_hit(**standard_hit_config())
        time.sleep(15)
        assert with_cleanup.disable_hit(hit['id'])

    def test_disable_hit_with_invalid_hit_id_raises(self, mturk):
        with pytest.raises(MTurkServiceException):
            mturk.disable_hit('dud')

    def test_get_hit_with_valid_hit_id(self, with_cleanup):
        hit = with_cleanup.create_hit(**standard_hit_config())
        retrieved = with_cleanup.get_hit(hit['id'])
        assert hit == retrieved

    def test_get_hits_returns_all_by_default(self, with_cleanup):
        hit = with_cleanup.create_hit(**standard_hit_config())
        time.sleep(15)  # Indexing required...
        hit_ids = [h['id'] for h in with_cleanup.get_hits()]
        assert hit['id'] in hit_ids

    def test_get_hits_excludes_based_on_filter(self, with_cleanup):
        hit1 = with_cleanup.create_hit(**standard_hit_config())
        hit2 = with_cleanup.create_hit(**standard_hit_config(title='HIT Two'))
        time.sleep(15)  # Indexing required...
        hit_ids = [
            h['id'] for h in with_cleanup.get_hits(lambda h: 'Two' in h['title'])
        ]
        assert hit1['id'] not in hit_ids
        assert hit2['id'] in hit_ids

    def test_create_and_dispose_qualification_type(self, with_cleanup):
        result = with_cleanup.create_qualification_type(
            name=generate_random_id(size=32),
            description=TEST_QUALIFICATION_DESCRIPTION,
            status='Active',
        )

        assert isinstance(result['id'], unicode)
        assert result['status'] == u'Active'
        assert with_cleanup.dispose_qualification_type(result['id'])

    def test_create_qualification_type_with_existing_name_raises(self, with_cleanup, qtype):
        with pytest.raises(DuplicateQualificationNameError):
            with_cleanup.create_qualification_type(qtype['name'], 'desc', 'Active')

    def test_get_qualification_type_by_name_with_valid_name(self, with_cleanup, qtype):
        result = with_cleanup.get_qualification_type_by_name(qtype['name'])
        assert qtype == result

    def test_get_qualification_type_by_name_no_match(self, with_cleanup, qtype):
        # First query can be very slow, since the qtype was just added:
        with_cleanup.max_wait_secs = 0
        result = with_cleanup.get_qualification_type_by_name('nonsense')
        assert result is None

    def test_get_qualification_type_by_name_returns_shortest_if_multi(self,
                                                                      with_cleanup,
                                                                      qtype):
        substr_name = qtype['name'][:-1]  # one char shorter name
        qtype2 = with_cleanup.create_qualification_type(
            name=substr_name,
            description=TEST_QUALIFICATION_DESCRIPTION,
            status='Active',
        )
        self.loop_until_2_quals(with_cleanup, substr_name)  # wait for indexing
        result = with_cleanup.get_qualification_type_by_name(substr_name)
        assert result['id'] == qtype2['id']
        with_cleanup.dispose_qualification_type(qtype2['id'])

    def test_get_qualification_type_by_name_must_match_exact_if_multi(self,
                                                                      with_cleanup,
                                                                      qtype):
        substr_name = qtype['name'][:-1]  # one char shorter name
        qtype2 = with_cleanup.create_qualification_type(
            name=substr_name,
            description=TEST_QUALIFICATION_DESCRIPTION,
            status='Active',
        )
        self.loop_until_2_quals(with_cleanup, substr_name)  # wait for indexing
        not_exact = substr_name[:-1]
        with pytest.raises(MTurkServiceException):
            with_cleanup.get_qualification_type_by_name(not_exact)

        with_cleanup.dispose_qualification_type(qtype2['id'])


@pytest.mark.mturk
@pytest.mark.mturkworker
@pytest.mark.skipif(not pytest.config.getvalue("mturkfull"),
                    reason="--mturkfull was not specified")
class TestMTurkServiceWithRequesterAndWorker(object):

    def test_can_assign_new_qualification(self, with_cleanup, worker_id, qtype):
        assert with_cleanup.assign_qualification(qtype['id'], worker_id, score=2)
        assert with_cleanup.get_qualification_score(qtype['id'], worker_id) == 2

    def test_can_update_existing_qualification(self, with_cleanup, worker_id, qtype):
        with_cleanup.assign_qualification(qtype['id'], worker_id, score=2)
        with_cleanup.update_qualification_score(qtype['id'], worker_id, score=3)

        assert with_cleanup.get_qualification_score(qtype['id'], worker_id) == 3

    def test_getting_invalid_qualification_score_raises(self, with_cleanup, worker_id):
        with pytest.raises(MTurkServiceException) as execinfo:
            with_cleanup.get_qualification_score('NONEXISTENT', worker_id)
        assert execinfo.match('QualificationType NONEXISTENT does not exist')

    def test_retrieving_revoked_qualifications_raises(self, with_cleanup, worker_id, qtype):
        with_cleanup.assign_qualification(qtype['id'], worker_id, score=2)
        with_cleanup.revoke_qualification(qtype['id'], worker_id)

        with pytest.raises(MTurkServiceException):
            with_cleanup.get_qualification_score(qtype['id'], worker_id)

    def test_get_workers_with_qualification(self, with_cleanup, worker_id, qtype):
        with_cleanup.assign_qualification(qtype['id'], worker_id, score=2)
        workers = with_cleanup.get_workers_with_qualification(qtype['id'])

        assert worker_id in [w['id'] for w in workers]

    def test_set_qualification_score_with_new_qualification(self, with_cleanup, worker_id, qtype):
        with_cleanup.set_qualification_score(qtype['id'], worker_id, score=2)

        assert with_cleanup.get_qualification_score(qtype['id'], worker_id) == 2

    def test_set_qualification_score_with_existing_qualification(self,
                                                                 with_cleanup,
                                                                 worker_id,
                                                                 qtype):
        with_cleanup.assign_qualification(qtype['id'], worker_id, score=2)
        with_cleanup.set_qualification_score(qtype['id'], worker_id, score=3)

        assert with_cleanup.get_qualification_score(qtype['id'], worker_id) == 3

    def test_get_current_qualification_score(self, with_cleanup, worker_id, qtype):
        with_cleanup.assign_qualification(qtype['id'], worker_id, score=2)

        result = with_cleanup.get_current_qualification_score(qtype['name'], worker_id)

        assert result['qtype']['id'] == qtype['id']
        assert result['score'] == 2

    def test_get_current_qualification_score_worker_unscored(self, with_cleanup, worker_id, qtype):
        result = with_cleanup.get_current_qualification_score(qtype['name'], worker_id)

        assert result['qtype']['id'] == qtype['id']
        assert result['score'] is None

    def test_increment_qualification_score(self, with_cleanup, worker_id, qtype):
        with_cleanup.assign_qualification(qtype['id'], worker_id, score=2)
        result = with_cleanup.increment_qualification_score(qtype['name'], worker_id)

        assert result['qtype']['id'] == qtype['id']
        assert result['score'] == 3

    def test_increment_qualification_score_worker_unscored(self, with_cleanup, worker_id, qtype):
        result = with_cleanup.increment_qualification_score(qtype['name'], worker_id)

        assert result['qtype']['id'] == qtype['id']
        assert result['score'] == 1

    def test_increment_qualification_score_nonexistent_qual(self, with_cleanup, worker_id):
        with_cleanup.max_wait_secs = 0  # we know the name doesn't exist, so no need to wait
        with pytest.raises(QualificationNotFoundException):
            with_cleanup.increment_qualification_score(
                'NONEXISTENT', worker_id
            )


@pytest.mark.mturk
@pytest.mark.mturkworker
@pytest.mark.skipif(not pytest.config.getvalue("manual"),
                    reason="--manual was not specified")
class TestInteractive(object):

    def test_worker_can_see_hit_when_blacklist_not_in_qualifications(self,
                                                                     with_cleanup,
                                                                     worker_id,
                                                                     qtype):
        with_cleanup.assign_qualification(qtype['id'], worker_id, score=1)

        print 'MANUAL STEP: Check for qualification: "{}". (May be delay)'.format(qtype['name'])
        raw_input("Any key to continue...")

        hit = with_cleanup.create_hit(
            **standard_hit_config(title="Dallinger: No Blacklist"))

        print 'MANUAL STEP: Should be able to see "{}" as available HIT'.format(hit['title'])
        raw_input("Any key to continue...")

    def test_worker_cannot_see_hit_when_blacklist_in_qualifications(self,
                                                                    with_cleanup,
                                                                    worker_id,
                                                                    qtype):
        with_cleanup.assign_qualification(qtype['id'], worker_id, score=1)

        print 'MANUAL STEP: Check for qualification: "{}". (May be delay)'.format(qtype['name'])
        raw_input("Any key to continue...")

        hit = with_cleanup.create_hit(
            **standard_hit_config(title="Dallinger: Blacklist", blacklist=[qtype['name']])
        )

        print 'MANUAL STEP: Should NOT be able to see "{}"" as available HIT'.format(hit['title'])
        raw_input("Any key to continue...")

        pass


@pytest.fixture
def with_mock(mturk):
    mocked_mturk = mock.Mock(spec=mturk.mturk)
    mturk.mturk = mocked_mturk
    return mturk


class TestMTurkServiceWithFakeConnection(object):

    def test_is_sandbox_by_default(self, with_mock):
        assert with_mock.is_sandbox

    def test_host_server_is_sandbox_by_default(self, with_mock):
        assert 'sandbox' in with_mock.host

    def test_host_server_is_production_if_sandbox_false(self, with_mock):
        with_mock.is_sandbox = False
        assert 'sandbox' not in with_mock.host

    def test_check_credentials_converts_response_to_boolean_true(self, with_mock):
        with_mock.mturk.configure_mock(
            **{'get_account_balance.return_value': fake_balance_response()}
        )
        assert with_mock.check_credentials() is True

    def test_check_credentials_calls_get_account_balance(self, with_mock):
        with_mock.mturk.configure_mock(
            **{'get_account_balance.return_value': fake_balance_response()}
        )
        with_mock.check_credentials()
        with_mock.mturk.get_account_balance.assert_called_once()

    def test_check_credentials_bad_credentials(self, with_mock):
        with_mock.mturk.configure_mock(
            **{'get_account_balance.side_effect': MTurkRequestError(1, 'ouch')}
        )
        with pytest.raises(MTurkRequestError):
            with_mock.check_credentials()

    def test_check_credentials_no_creds_set_raises(self, with_mock):
        creds = {
            'aws_access_key_id': '',
            'aws_secret_access_key': '',
            'region_name': ''
        }
        service = MTurkService(**creds)
        with pytest.raises(MTurkServiceException):
            service.check_credentials()

    def test_build_hit_qualifications_with_blacklist(self, with_mock):
        qtypes = fake_list_qualification_types_response()
        qtype_id = qtypes['QualificationTypes'][0]['QualificationTypeId']
        with_mock.mturk.list_qualification_types.return_value = qtypes
        quals = with_mock.build_hit_qualifications(
            95, False, blacklist=[qtype_id]
        )
        assert quals[-1]['QualificationTypeId'] == qtype_id
        assert quals[-1]['Comparator'] == "DoesNotExist"

    def test_build_hit_qualifications_with_region_restriction(self, with_mock):
        quals = with_mock.build_hit_qualifications(
            95, restrict_to_usa=True, blacklist=None
        )
        assert quals[-1]['Comparator'] == "EqualTo"
        assert quals[-1]['LocaleValues'] == [{'Country': 'US'}]

    def test_get_qualification_type_by_name_with_invalid_name_returns_none(self, with_mock):
        with_mock.mturk.list_qualification_types.return_value = {'QualificationTypes': []}
        with_mock.max_wait_secs = 1
        assert with_mock.get_qualification_type_by_name("foo") is None

    def test_get_qualification_type_by_name_raises_if_not_unique_and_not_exact_match(self,
                                                                                     with_mock):
        two_quals = [
            fake_qualification_type_response()['QualificationType'],
            fake_qualification_type_response()['QualificationType']
        ]
        qtypes = fake_list_qualification_types_response(qtypes=two_quals)
        with_mock.mturk.list_qualification_types.return_value = qtypes
        with pytest.raises(MTurkServiceException):
            with_mock.get_qualification_type_by_name(
                qtypes['QualificationTypes'][0]['Name'][:6]
            )

    def test_get_qualification_type_by_name_works_if_not_unique_but_is_exact_match(self,
                                                                                   with_mock):
        qtypes = fake_list_qualification_types_response()
        with_mock.mturk.list_qualification_types.return_value = qtypes
        assert with_mock.get_qualification_type_by_name(
            qtypes['QualificationTypes'][0]['Name']
        )['name'] == qtypes['QualificationTypes'][0]['Name']

    def test_register_hit_type(self, with_mock):
        quals = with_mock.build_hit_qualifications(95, True, None)
        config = {
            'title': 'Test Title',
            'description': 'Test Description',
            'keywords': ['testkw1', 'testkw2'],
            'reward': .01,
            'duration_hours': .25,
            'qualifications': quals
        }
        with_mock.mturk.configure_mock(**{
            'get_account_balance.return_value': fake_balance_response(),
            'create_hit_type.return_value': fake_hit_type_response(),
        })

        with_mock.register_hit_type(**config)

        with_mock.mturk.create_hit_type.assert_called_once_with(
            Title='Test Title',
            Description='Test Description',
            Reward='0.01',
            AssignmentDurationInSeconds=datetime.timedelta(hours=.25).seconds,
            Keywords='testkw1,testkw2',
            AutoApprovalDelayInSeconds=0,
            QualificationRequirements=quals
        )

    def test_set_rest_notification(self, with_mock):
        url = 'https://url-of-notification-route'
        hit_type_id = 'fake hittype id'
        with_mock.mturk.configure_mock(**{
            'set_rest_notification.return_value': ResultSet(),
        })

        with_mock.set_rest_notification(url, hit_type_id)

        with_mock.mturk.set_rest_notification.assert_called_once()

    def test_create_hit_calls_underlying_mturk_method(self, with_mock):
        with_mock.mturk.configure_mock(**{
            'create_hit_type.return_value': fake_hit_type_response(),
            'create_hit_with_hit_type.return_value': fake_hit_response(),
        })
        with_mock.create_hit(**standard_hit_config())

        with_mock.mturk.create_hit_with_hit_type.assert_called_once()

    def test_create_hit_translates_response_back_from_mturk(self, with_mock):
        with_mock.mturk.configure_mock(**{
            'create_hit_type.return_value': fake_hit_type_response(),
            'create_hit_with_hit_type.return_value': fake_hit_response(),
        })

        hit = with_mock.create_hit(**standard_hit_config())

        assert hit['max_assignments'] == 1
        assert hit['reward'] == .01
        assert hit['keywords'] == ['testkw1', 'testkw2']
        assert isinstance(hit['created'], datetime.datetime)
        assert isinstance(hit['expiration'], datetime.datetime)

    def test_extend_hit(self, with_mock):
        with_mock.mturk.configure_mock(**{
            'create_additional_assignments_for_hit.return_value': {},
            'get_hit.return_value': fake_hit_response(),
        })

        with_mock.extend_hit(hit_id='hit1', number=2, duration_hours=1.0)

        with_mock.mturk.create_additional_assignments_for_hit.assert_called_once()
        with_mock.mturk.update_expiration_for_hit.assert_called_once()

    def test_extend_hit_wraps_exception_helpfully(self, with_mock):
        with_mock.mturk.configure_mock(**{
            'create_additional_assignments_for_hit.side_effect': Exception("Boom!"),
        })
        with pytest.raises(MTurkServiceException) as execinfo:
            with_mock.extend_hit(hit_id='hit1', number=2, duration_hours=1.0)

        assert execinfo.match("Error: failed to add 2 assignments to HIT: Boom!")

    def test_disable_hit(self, with_mock):
        with_mock.mturk.configure_mock(**{
            'update_expiration_for_hit.return_value': True,
            'delete_hit.return_value': {},
        })

        with_mock.disable_hit('some hit')

        with_mock.mturk.delete_hit.assert_called_once_with(HITId='some hit')

    def test_get_hits_returns_all_by_default(self, with_mock):
        hr1 = fake_hit_response(Title='One')[0]
        ht2 = fake_hit_response(Title='Two')[0]

        with_mock.mturk.configure_mock(**{
            'get_all_hits.return_value': as_resultset([hr1, ht2]),
        })

        assert len(list(with_mock.get_hits())) == 2

    def test_get_hits_excludes_based_on_filter(self, with_mock):
        hr1 = fake_hit_response(Title='HIT One')[0]
        ht2 = fake_hit_response(Title='HIT Two')[0]
        with_mock.mturk.configure_mock(**{
            'get_all_hits.return_value': as_resultset([hr1, ht2]),
        })

        hits = list(with_mock.get_hits(lambda h: 'Two' in h['title']))

        assert len(hits) == 1
        assert hits[0]['title'] == 'HIT Two'

    def test_grant_bonus_translates_values_and_calls_wrapped_mturk(self, with_mock):
        fake_assignment = Assignment(None)
        fake_assignment.WorkerId = 'some worker id'
        with_mock.mturk.configure_mock(**{
            'grant_bonus.return_value': ResultSet(),
            'get_assignment.return_value': as_resultset(fake_assignment),
        })

        with_mock.grant_bonus(
            assignment_id='some assignment id',
            amount=2.99,
            reason='above and beyond'
        )

        with_mock.mturk.grant_bonus.assert_called_once_with(
            'some worker id',
            'some assignment id',
            mock.ANY,  # can't compare Price objects :-(
            'above and beyond'
        )

    def test_grant_bonus_wraps_exception_helpfully(self, with_mock):
        fake_assignment = Assignment(None)
        fake_assignment.WorkerId = 'some worker id'
        with_mock.mturk.configure_mock(**{
            'get_assignment.return_value': as_resultset(fake_assignment),
            'grant_bonus.side_effect': MTurkRequestError(1, "Boom!"),
        })
        with pytest.raises(MTurkServiceException) as execinfo:
            with_mock.grant_bonus(
                assignment_id='some assignment id',
                amount=2.99,
                reason='above and beyond'
            )

            assert execinfo.match(
                "Failed to pay assignment some assignment id bonus of 2.99"
            )

    def test_approve_assignment(self, with_mock):
        with_mock.mturk.configure_mock(**{
            'approve_assignment.return_value': ResultSet(),
        })

        assert with_mock.approve_assignment('fake id') is True
        with_mock.mturk.approve_assignment.assert_called_once_with(
            'fake id', feedback=None
        )

    def test_approve_assignment_wraps_exception_helpfully(self, with_mock):
        with_mock.mturk.configure_mock(**{
            'approve_assignment.side_effect': MTurkRequestError(1, "Boom!")
        })

        with pytest.raises(MTurkServiceException) as execinfo:
            with_mock.approve_assignment('fake_id')

        assert execinfo.match("Failed to approve assignment fake_id")

    def test_create_qualification_type(self, with_mock):
        with_mock.mturk.configure_mock(**{
            'create_qualification_type.return_value': fake_qualification_type_response(),
        })
        result = with_mock.create_qualification_type('name', 'desc', 'status')
        with_mock.mturk.create_qualification_type.assert_called_once_with(
            'name', 'desc', 'status'
        )
        assert isinstance(result['created'], datetime.datetime)

    def test_create_qualification_type_raises_if_invalid(self, with_mock):
        response = fake_qualification_type_response()
        response[0].IsValid = 'False'
        with_mock.mturk.configure_mock(**{
            'create_qualification_type.return_value': response,
        })
        with pytest.raises(MTurkServiceException):
            with_mock.create_qualification_type('name', 'desc', 'status')

    def test_create_qualification_type_raises_on_duplicate_name(self, with_mock):
        error = MTurkRequestError(
            1, u'already created a QualificationType with this name'
        )
        error.message = error.reason
        with_mock.mturk.configure_mock(**{
            'create_qualification_type.side_effect': error,
        })
        with pytest.raises(DuplicateQualificationNameError):
            with_mock.create_qualification_type('name', 'desc', 'status')

    def test_assign_qualification(self, with_mock):
        with_mock.mturk.configure_mock(**{
            'assign_qualification.return_value': ResultSet(),
        })
        assert with_mock.assign_qualification('qid', 'worker', 'score')
        with_mock.mturk.assign_qualification.assert_called_once_with(
            'qid', 'worker', 'score', False
        )

    def test_update_qualification_score(self, with_mock):
        with_mock.mturk.configure_mock(**{
            'update_qualification_score.return_value': ResultSet(),
        })
        assert with_mock.update_qualification_score('qid', 'worker', 'score')
        with_mock.mturk.update_qualification_score.assert_called_once_with(
            'qid', 'worker', 'score'
        )

    def test_dispose_qualification_type(self, with_mock):
        with_mock.mturk.configure_mock(**{
            'dispose_qualification_type.return_value': ResultSet(),
        })
        assert with_mock.dispose_qualification_type('qid')
        with_mock.mturk.dispose_qualification_type.assert_called_once_with(
            'qid'
        )

    def test_get_workers_with_qualification(self, with_mock):
        with_mock.mturk.configure_mock(**{
            'get_qualifications_for_qualification_type.side_effect': [
                fake_qualification_response(), ResultSet()
            ],
        })
        expected = [
            mock.call('qid', page_number=1, page_size=100),
            mock.call('qid', page_number=2, page_size=100)
        ]
        # need to unroll the iterator:
        list(with_mock.get_workers_with_qualification('qid'))
        calls = with_mock.mturk.get_qualifications_for_qualification_type.call_args_list
        assert calls == expected

    def test_set_qualification_score_with_existing_qualification(self, with_mock):
        with_mock.get_workers_with_qualification = mock.Mock(
            return_value=[{'id': 'workerid', 'score': 2}]
        )
        with_mock.update_qualification_score = mock.Mock(return_value=True)

        assert with_mock.set_qualification_score('qid', 'workerid', 4)
        with_mock.get_workers_with_qualification.assert_called_once_with('qid')
        with_mock.update_qualification_score.assert_called_once_with(
            'qid', 'workerid', 4
        )

    def test_set_qualification_score_with_new_qualification(self, with_mock):
        with_mock.get_workers_with_qualification = mock.Mock(return_value=[])
        with_mock.assign_qualification = mock.Mock(return_value=True)

        assert with_mock.set_qualification_score('qid', 'workerid', 4)
        with_mock.get_workers_with_qualification.assert_called_once_with('qid')
        with_mock.assign_qualification.assert_called_once_with(
            'qid', 'workerid', 4, False
        )

    def test_get_current_qualification_score(self, with_mock):
        worker_id = 'some worker id'
        with_mock.get_qualification_type_by_name = mock.Mock(return_value={'id': 'qid'})
        with_mock.mturk.get_all_qualifications_for_qual_type = mock.Mock(
            return_value=[mock.Mock(SubjectId=worker_id, IntegerValue='1')]
        )

        result = with_mock.get_current_qualification_score('some name', worker_id)

        assert result['qtype'] == {'id': 'qid'}
        assert result['score'] == 1

    def test_get_current_qualification_score_worker_unscored(self, with_mock):
        worker_id = 'some worker id'
        with_mock.get_qualification_type_by_name = mock.Mock(return_value={'id': 'qid'})
        with_mock.mturk.get_all_qualifications_for_qual_type = mock.Mock(
            return_value=[mock.Mock(SubjectId='other worker id', IntegerValue='1')]
        )

        result = with_mock.get_current_qualification_score('some name', worker_id)

        assert result['qtype'] == {'id': 'qid'}
        assert result['score'] is None

    def test_increment_qualification_score_for_worker_with_score(self, with_mock):
        worker_id = 'some worker id'
        fake_score = {'qtype': {'id': 'qtype_id'}, 'score': 2}
        with_mock.get_current_qualification_score = mock.Mock(
            return_value=fake_score)

        result = with_mock.increment_qualification_score('some qual', worker_id)

        assert result['score'] == 3
        with_mock.mturk.update_qualification_score.assert_called_once_with(
            'qtype_id', worker_id, 3
        )

    def test_increment_qualification_score_for_worker_with_no_score(self, with_mock):
        worker_id = 'some worker id'
        fake_score = {'qtype': {'id': 'qtype_id'}, 'score': None}
        with_mock.get_current_qualification_score = mock.Mock(
            return_value=fake_score)

        result = with_mock.increment_qualification_score('some qual', worker_id)

        assert result['score'] == 1
        with_mock.mturk.assign_qualification.assert_called_once_with(
            'qtype_id', worker_id, 1, False
        )

    def test_increment_qualification_score_nonexisting_qual_raises(self, with_mock):
        worker_id = 'some worker id'
        with_mock.get_qualification_type_by_name = mock.Mock(return_value=None)

        with pytest.raises(QualificationNotFoundException):
            with_mock.increment_qualification_score('some qual', worker_id)
