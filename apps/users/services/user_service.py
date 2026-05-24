from apps.users.repositories.user_repository import UserRepository


class UserService:

    @staticmethod
    def get_user(user_id):
        return UserRepository.get_user_by_id(user_id)

    @staticmethod
    def list_users():
        return UserRepository.list_users()

    @staticmethod
    def update_user(user, validated_data):
        profile_data = validated_data.pop("profile", None)

        user = UserRepository.update_user(user, validated_data)

        if profile_data is not None:
            UserRepository.update_profile(user, profile_data)
            # Invalidate cached profile relations on the in-memory user instance
            for attr in ['influencer_profile', 'marketer_profile', 'brand_profile']:
                user._state.fields_cache.pop(attr, None)

        return user

    @staticmethod
    def delete_user(user):
        UserRepository.delete_user(user)

    @staticmethod
    def search_influencers(name=None, category=None, niche=None):
        return UserRepository.search_influencers(name=name, category=category, niche=niche)
