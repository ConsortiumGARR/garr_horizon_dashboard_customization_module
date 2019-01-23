import horizon

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
    unregister_panel(dashboard_slug, panel_slug)

