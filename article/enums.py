from enum import Enum, unique

@unique
class CategoryChoices(Enum):
    BUSINESS = 'business'
    ENTERTAINMENT = 'entertainment'
    GENERAL = 'general'
    HEALTH = 'health'
    SCIENCE = 'science'
    SPORTS = 'sports'
    TECHNOLOGY = 'technology'

categories = [category.value for category in CategoryChoices]
