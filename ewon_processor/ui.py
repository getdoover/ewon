import logging

from pydoover import ui


def tag_to_element(settings, tag):

    if not tag:
        return None

    name = settings.get("tag_name", tag.tag_name)
    display_name = settings.get("display_name", tag.description)
    ranges = settings.get("ranges", None)
    form = settings.get("form", None)
    dec_precision = settings.get("dec_precision", None)

    dataType = tag.tag_data_type

    if dataType == "Bool":
        return ui.BooleanVariable(name, display_name)
    
    elif dataType == "Float":
        return ui.NumericVariable(
            name, display_name,
            dec_precision=dec_precision,
            ranges=ranges,
            form=form,
        )
    
    return None


def construct_ui(processor, ewon):

    ewon_ui_settings = processor.get_ewon_ui_settings()

    ewon_tags = ewon.tags

    ui_elems = []

    if "multiplot" in ewon_ui_settings:
        series = ewon_ui_settings["multiplot"]["series"]
        series_active = ewon_ui_settings["multiplot"]["default_active"]

        multiplot = ui.Multiplot("overviewPlot", "Overview",
            series=series,
            series_active=series_active,
        )
        ui_elems.append(multiplot)

    if "tags" in ewon_ui_settings:
        for ui_tag in ewon_ui_settings["tags"]:

            ## Find the corresponding tag
            tag = ewon.get_tag(ui_tag["tag_name"])
            ## pop it from the list remaining
            ewon_tags.pop(tag)

            element = tag_to_element(ui_tag, tag)
            if element:
                ui_elems.append(element)


    if "exclude_tags" in ewon_ui_settings:
        for tag in ewon_ui_settings["exclude_tags"]:
            ## Find the corresponding tag
            tag = ewon.get_tag(tag)
            ## pop it from the list remaining
            ewon_tags.pop(tag)

    if "auto_include" in ewon_ui_settings and not ewon_ui_settings["auto_include"]:
        return ui_elems
    ## Otherwise, we will include all remaining tags

    ## Add any remaining tags
    for tag in ewon_tags:
        element = tag_to_element({}, tag)
        if element:
            ui_elems.append(element)

    ui_elems.append(
        ui.ConnectionInfo("connectionInfo", "Connection Info",
            connection_type=ui.ConnectionType.periodic,
            connection_period=(60*60), # 1 hour
            next_connection=(60*60), # 1 hour
            allowed_misses=6,
        )
    )

    return ui_elems