from pydoover.tags import Tag, Tags

from .app_config import EwonConfig


class EwonTags(Tags):
    config: EwonConfig

    warning_active = Tag("boolean", default=False)
    warning_string = Tag("string", default="Warning")

    last_ewon_transaction_id = Tag("number", default=0)

    async def setup(self):
        excluded = [t.value for t in self.config.exclude.elements]
        # self.tags = [
        #     t.to_ui_element()
        #     for t in self.config.tags
        #     if t.tag_name not in excluded
        # ]
        for tag in self.config.tags:
            if tag.tag_name in excluded:
                continue

            self.add_tag(tag.tag_name, Tag("number"))
