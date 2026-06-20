# Source: d2items_for_sale (itemnow.com)

## URL

https://itemnow.com/product-category/diablo-2/runes/

## Type

WordPress-based cash/RMT marketplace. Static HTML with WordPress REST API exposed.

## Rune Prices

All 33 runes mentioned in page text. Prices not directly visible in static HTML — the WordPress shop likely loads prices via WooCommerce AJAX.

## Static vs Dynamic

Partially static. WordPress site with WooCommerce. Product pages likely have server-rendered prices.

## Segmentation

Server-based filter switching via URL parameters:
- `?server=d2r-non-ladder`
- `?server=d2r-hc-non-ladder`
- `?server=d2r-hc-ladder`

Segments: ladder, non-ladder, hardcore non-ladder

## API Clues

WordPress REST API exposed:
- `https://itemnow.com/wp-json/wp/v2/product_cat/99`
- `https://api.w.org/`

The WP API could potentially be queried for product data with prices.

## Recommendation

**External cash-market comparison only.** WordPress REST API may provide structured product data including prices. Worth exploring the WP REST API endpoints.

## Downloads Needed

- Individual product pages for runes (likely have prices)
- WP REST API root at `https://itemnow.com/wp-json/` to discover endpoints
