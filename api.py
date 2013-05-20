from django_odc.models import Dataset


def get_datasets_for_user(user, include_user_group_linked=True):
    return [d.to_dict() for d in Dataset.GetForUser(
        user,
        include_user_group_linked=include_user_group_linked)]


def get_dataset_for_user_by_id(user, dataset_id, include_user_group_linked=True):
    dataset = _get_dataset_for_user_by_id(user, dataset_id, include_user_group_linked)
    if not dataset:
        return None
    return dataset.to_dict()


def get_dataset_statistics_by_dataset_id(user, dataset_id):
    dataset = _get_dataset_for_user_by_id(user, dataset_id, True)
    if not dataset:
        return None
    return dataset.get_statistics(format_for_display=True)


def run_query_for_dataset(user, dataset_id, search_data):
    dataset = _get_dataset_for_user_by_id(user, dataset_id, True)
    if not dataset:
        return None
    return dataset.run_query(search_data)


def _get_dataset_for_user_by_id(user, dataset_id, include_user_group_linked=True):
    dataset = Dataset.GetById(dataset_id)
    if not dataset:
        return None
    if not include_user_group_linked and dataset.user != user:
        return None
    if dataset.user != user and not dataset.user_is_in_user_groups(user):
        return None
    return dataset


