from pydoover.tags import Tag, Tags

from .app_config import EwonCommonConfig
from .tags import transform_tag_name


class EwonTags(Tags):
    config: EwonCommonConfig

    warning_hidden = Tag("boolean", default=True)
    warning_string = Tag("string", default="Warning")

    last_ewon_transaction_id = Tag("number", default=0)

    async def setup(self):
        excluded = [t.value for t in self.config.exclude.elements]
        for tag in self.config.tags.elements:
            if tag.tag_name.value in excluded:
                continue

            self.add_tag(transform_tag_name(tag.tag_name.value), Tag("number"))
