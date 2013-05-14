from django_odc.models import Dataset


def get_datasets_for_user(user):
    return [d.to_dict() for d in Dataset.GetForUser(user)]


def get_dataset_for_user_by_id(user, dataset_id):
    dataset = Dataset.GetById(dataset_id)
    if not dataset or dataset.user != user:
        return None
    return dataset.to_dict()


def get_dataset_statistics_by_dataset_id(user, dataset_id):
    dataset = Dataset.GetById(dataset_id)
    if not dataset or dataset.user != user:
        return None
    return dataset.get_statistics(format_for_display=True)


def run_query_for_dataset(user, dataset_id, search_data):
    dataset = Dataset.GetById(dataset_id)
    if not dataset or dataset.user != user:
        return None
    return dataset.run_query(search_data)