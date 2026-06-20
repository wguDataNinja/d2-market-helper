import json
import pandas as pd
import ipywidgets as widgets
from IPython.display import display, clear_output
from datetime import datetime, timedelta
from collections import Counter
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots


class RuneTradeExplorer:
    def __init__(self, json_file_path):
        """Initialize the trade explorer with data from JSON file."""
        with open(json_file_path, 'r') as f:
            self.raw_data = json.load(f)

        self.trades_df = self._parse_trades_to_dataframe()
        self.setup_gui()

    def _parse_trades_to_dataframe(self):
        """Convert JSON data to a structured DataFrame for easier analysis."""
        trades = []

        for offer_rune, listings in self.raw_data["Runes"].items():
            for entry in listings:
                if not entry.get("price"):
                    continue

                # Basic trade info
                base_info = {
                    'offer_rune': offer_rune,
                    'seller': entry['seller'],
                    'offer_quantity': entry['quantity'],
                    'updated_at': pd.to_datetime(entry['updated_at']),
                    'trade_type': 'AND' if len(entry['price']) > 1 else 'Single',
                    'ask_items_count': len(entry['price'])
                }

                # For each ask item in the price
                for ask_item in entry['price']:
                    trade_record = base_info.copy()
                    trade_record.update({
                        'ask_item': ask_item['name'],
                        'ask_quantity': ask_item['quantity']
                    })
                    trades.append(trade_record)

        df = pd.DataFrame(trades)
        df['days_ago'] = (pd.Timestamp.now() - df['updated_at']).dt.days
        return df

    def setup_gui(self):
        """Create the interactive GUI components."""
        # Filter widgets
        self.offer_filter = widgets.SelectMultiple(
            options=['All'] + sorted(self.trades_df['offer_rune'].unique()),
            value=['All'],
            description='Offer Runes:',
            style={'description_width': 'initial'},
            layout=widgets.Layout(width='300px', height='120px')
        )

        self.ask_filter = widgets.SelectMultiple(
            options=['All'] + sorted(self.trades_df['ask_item'].unique()),
            value=['All'],
            description='Ask Items:',
            style={'description_width': 'initial'},
            layout=widgets.Layout(width='300px', height='120px')
        )

        self.trade_type_filter = widgets.SelectMultiple(
            options=['All', 'Single', 'AND'],
            value=['All'],
            description='Trade Type:',
            style={'description_width': 'initial'}
        )

        self.days_filter = widgets.IntRangeSlider(
            value=[0, self.trades_df['days_ago'].max()],
            min=0,
            max=self.trades_df['days_ago'].max(),
            description='Days Ago:',
            style={'description_width': 'initial'}
        )

        self.seller_search = widgets.Text(
            placeholder='Search seller name...',
            description='Seller:',
            style={'description_width': 'initial'}
        )

        # Display options
        self.view_mode = widgets.RadioButtons(
            options=['Summary Stats', 'Trade List', 'Charts', 'Price Analysis'],
            value='Summary Stats',
            description='View:',
            style={'description_width': 'initial'}
        )

        self.max_rows = widgets.IntSlider(
            value=50,
            min=10,
            max=500,
            step=10,
            description='Max Rows:',
            style={'description_width': 'initial'}
        )

        # Action buttons
        self.refresh_btn = widgets.Button(
            description='Refresh Data',
            button_style='primary',
            icon='refresh'
        )

        self.export_btn = widgets.Button(
            description='Export CSV',
            button_style='success',
            icon='download'
        )

        # Output area
        self.output = widgets.Output()

        # Event handlers
        self.refresh_btn.on_click(self._on_refresh)
        self.export_btn.on_click(self._on_export)

        # Auto-refresh on filter changes
        for widget in [self.offer_filter, self.ask_filter, self.trade_type_filter,
                       self.days_filter, self.seller_search, self.view_mode, self.max_rows]:
            widget.observe(self._on_filter_change, names='value')

    def _get_filtered_data(self):
        """Apply all filters to the data."""
        df = self.trades_df.copy()

        # Offer filter
        if 'All' not in self.offer_filter.value:
            df = df[df['offer_rune'].isin(self.offer_filter.value)]

        # Ask filter
        if 'All' not in self.ask_filter.value:
            df = df[df['ask_item'].isin(self.ask_filter.value)]

        # Trade type filter
        if 'All' not in self.trade_type_filter.value:
            df = df[df['trade_type'].isin(self.trade_type_filter.value)]

        # Days filter
        df = df[(df['days_ago'] >= self.days_filter.value[0]) &
                (df['days_ago'] <= self.days_filter.value[1])]

        # Seller search
        if self.seller_search.value:
            df = df[df['seller'].str.contains(self.seller_search.value, case=False, na=False)]

        return df

    def _display_summary_stats(self, df):
        """Display summary statistics."""
        print("📊 TRADE SUMMARY STATISTICS")
        print("=" * 50)

        # Basic stats
        total_trades = len(df.drop_duplicates(['offer_rune', 'seller', 'updated_at']))
        total_entries = len(df)
        unique_sellers = df['seller'].nunique()
        unique_offers = df['offer_rune'].nunique()
        unique_asks = df['ask_item'].nunique()

        print(f"Total Trade Entries: {total_entries:,}")
        print(f"Unique Trades: {total_trades:,}")
        print(f"Unique Sellers: {unique_sellers:,}")
        print(f"Unique Offer Runes: {unique_offers}")
        print(f"Unique Ask Items: {unique_asks}")

        # Trade type breakdown
        trade_type_counts = df.groupby('trade_type').size()
        print(f"\n📈 Trade Type Breakdown:")
        for trade_type, count in trade_type_counts.items():
            pct = (count / total_entries) * 100
            print(f"  {trade_type}: {count:,} ({pct:.1f}%)")

        # Top offers
        print(f"\n🎯 Top 10 Offered Runes:")
        offer_counts = df['offer_rune'].value_counts().head(10)
        for rune, count in offer_counts.items():
            print(f"  {rune}: {count}")

        # Top asks
        print(f"\n💰 Top 10 Requested Items:")
        ask_counts = df['ask_item'].value_counts().head(10)
        for item, count in ask_counts.items():
            print(f"  {item}: {count}")

        # Time analysis
        df_recent = df[df['days_ago'] <= 7]
        print(f"\n⏰ Recent Activity (Last 7 days): {len(df_recent):,} entries")

        if len(df_recent) > 0:
            print("  Top recent offers:")
            recent_offers = df_recent['offer_rune'].value_counts().head(5)
            for rune, count in recent_offers.items():
                print(f"    {rune}: {count}")

    def _display_trade_list(self, df):
        """Display detailed trade list."""
        print("📋 DETAILED TRADE LIST")
        print("=" * 80)

        # Group by unique trades to avoid duplicates
        trades = df.groupby(['offer_rune', 'seller', 'updated_at']).agg({
            'offer_quantity': 'first',
            'trade_type': 'first',
            'ask_item': lambda x: ' + '.join(f"{row['ask_item']} ({row['ask_quantity']})"
                                             for _, row in df[df.index.isin(x.index)].iterrows()),
            'days_ago': 'first'
        }).reset_index()

        trades = trades.head(self.max_rows.value)

        for _, trade in trades.iterrows():
            print(f"🔸 {trade['offer_rune']} (x{trade['offer_quantity']}) by {trade['seller']}")
            print(f"   Wants: {trade['ask_item']}")
            print(f"   Type: {trade['trade_type']} | {trade['days_ago']} days ago")
            print(f"   Updated: {trade['updated_at'].strftime('%Y-%m-%d %H:%M')}")
            print()

    def _display_charts(self, df):
        """Display interactive charts."""
        print("📊 TRADE ANALYSIS CHARTS")
        print("=" * 40)

        # Chart 1: Offer distribution
        fig1 = px.bar(
            df['offer_rune'].value_counts().head(15),
            title="Top 15 Offered Runes",
            labels={'index': 'Rune', 'value': 'Count'}
        )
        fig1.show()

        # Chart 2: Ask distribution
        fig2 = px.bar(
            df['ask_item'].value_counts().head(15),
            title="Top 15 Requested Items",
            labels={'index': 'Item', 'value': 'Count'}
        )
        fig2.show()

        # Chart 3: Trade type over time
        time_data = df.groupby([df['updated_at'].dt.date, 'trade_type']).size().reset_index()
        time_data.columns = ['date', 'trade_type', 'count']

        fig3 = px.line(
            time_data,
            x='date',
            y='count',
            color='trade_type',
            title="Trade Activity Over Time"
        )
        fig3.show()

        # Chart 4: AND trade composition
        if len(df[df['trade_type'] == 'AND']) > 0:
            and_items = df[df['trade_type'] == 'AND']['ask_item'].value_counts().head(10)
            fig4 = px.pie(
                values=and_items.values,
                names=and_items.index,
                title="Most Common Items in AND Trades"
            )
            fig4.show()

    def _display_price_analysis(self, df):
        """Display price analysis and trends."""
        print("💹 PRICE ANALYSIS")
        print("=" * 40)

        # Most valuable offers (based on complexity of asks)
        print("🏆 Most Complex Trades (by ask variety):")
        complex_trades = df.groupby(['offer_rune', 'seller', 'updated_at']).agg({
            'ask_item': 'count',
            'trade_type': 'first'
        }).reset_index()
        complex_trades = complex_trades.sort_values('ask_item', ascending=False).head(10)

        for _, trade in complex_trades.iterrows():
            asks = df[(df['offer_rune'] == trade['offer_rune']) &
                      (df['seller'] == trade['seller']) &
                      (df['updated_at'] == trade['updated_at'])]
            ask_list = [f"{row['ask_item']} (x{row['ask_quantity']})" for _, row in asks.iterrows()]
            print(f"  {trade['offer_rune']} by {trade['seller']}")
            print(f"    Wants: {' + '.join(ask_list)}")
            print()

        # Price trends for popular items
        print("📈 Popular Ask Items Trends:")
        popular_asks = df['ask_item'].value_counts().head(5).index

        for item in popular_asks:
            item_df = df[df['ask_item'] == item]
            recent_count = len(item_df[item_df['days_ago'] <= 7])
            total_count = len(item_df)
            trend = "↗️" if recent_count / total_count > 0.3 else "↘️"
            print(f"  {item}: {total_count} total, {recent_count} recent {trend}")

    def _on_refresh(self, button):
        """Handle refresh button click."""
        self._on_filter_change(None)

    def _on_export(self, button):
        """Handle export button click."""
        df = self._get_filtered_data()
        filename = f"rune_trades_export_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
        df.to_csv(filename, index=False)
        with self.output:
            print(f"✅ Data exported to {filename}")

    def _on_filter_change(self, change):
        """Handle filter changes."""
        with self.output:
            clear_output(wait=True)
            df = self._get_filtered_data()

            if len(df) == 0:
                print("❌ No trades match the current filters.")
                return

            if self.view_mode.value == 'Summary Stats':
                self._display_summary_stats(df)
            elif self.view_mode.value == 'Trade List':
                self._display_trade_list(df)
            elif self.view_mode.value == 'Charts':
                self._display_charts(df)
            elif self.view_mode.value == 'Price Analysis':
                self._display_price_analysis(df)

    def display(self):
        """Display the complete GUI."""
        # Create layout
        filters_box = widgets.VBox([
            widgets.HTML("<h3>🔍 Filters</h3>"),
            widgets.HBox([self.offer_filter, self.ask_filter]),
            widgets.HBox([self.trade_type_filter, self.seller_search]),
            self.days_filter
        ])

        options_box = widgets.VBox([
            widgets.HTML("<h3>⚙️ Display Options</h3>"),
            self.view_mode,
            self.max_rows,
            widgets.HBox([self.refresh_btn, self.export_btn])
        ])

        controls = widgets.HBox([filters_box, options_box])

        full_gui = widgets.VBox([
            widgets.HTML("<h1>🏺 Rune Trade Explorer</h1>"),
            controls,
            widgets.HTML("<hr>"),
            self.output
        ])

        display(full_gui)

        # Initial load
        self._on_filter_change(None)

# Usage example:
# explorer = RuneTradeExplorer("/Users/buddy/Desktop/traderie/data/raw/raw_trades_pc_sc_nl.json")
# explorer.display()