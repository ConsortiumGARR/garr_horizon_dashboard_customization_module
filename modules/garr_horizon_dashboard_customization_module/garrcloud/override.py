import horizon
import horizon.base

dashboard_slug = 'admin'
panel_slugs = [
    'instances',
    'volumes',
    'images',
    'aggregates',
    'info',
    'networks',
    'routers',
    'defaults',
    'hypervisors',
    'metadata_defs',
    'flavors',
    'metering'
]

def unregister_panel(dashboard_slug, panel_slug):
    dashboard = horizon.get_dashboard(dashboard_slug)
    panel = dashboard.get_panel(panel_slug)
    dashboard.unregister(panel.__class__)

for panel_slug in panel_slugs:
    try:
        unregister_panel(dashboard_slug, panel_slug)
    except horizon.base.NotRegistered: # ignore missing slugs
        # TODO: log a meaningful message
        pass

