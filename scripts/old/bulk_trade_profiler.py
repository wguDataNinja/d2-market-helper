#!/usr/bin/env python3
"""
Bulk Distortion Profiler for Traderie Raw Trade Data

This script analyzes raw trade files to identify and quantify bulk pricing distortions
that corrupt the fair market value calculations.
"""

import json
import os
from collections import defaultdict, Counter
from datetime import datetime
import pandas as pd


def load_raw_trades(file_path):
    """Load raw trades from JSON file."""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception as e:
        print(f"Error loading {file_path}: {e}")
        return {}


def analyze_trade_patterns(raw_data, server_name):
    """Analyze trade patterns for bulk distortion detection."""

    # Initialize counters
    total_trades = 0
    trade_patterns = {
        'single_item_qty_1': 0,
        'single_item_bulk': 0,
        'multi_item_clean': 0,
        'multi_item_bulk': 0,
        'invalid': 0
    }

    # Tracking for analysis
    quantity_distribution = []
    price_quantity_distribution = []
    extreme_ratios = []
    highest_qty_trades = []
    item_bulk_frequency = defaultdict(int)
    suspicious_trades = []

    # Process each category (Runes, Gems, etc.)
    for category, items in raw_data.items():
        for item_name, trades in items.items():
            for trade in trades:
                total_trades += 1

                # Extract basic trade info
                quantity = trade.get('quantity', 0)
                price = trade.get('price', [])
                seller = trade.get('seller', 'unknown')
                updated_at = trade.get('updated_at', '')

                # Track quantity distributions
                quantity_distribution.append(quantity)

                # Calculate total price quantity
                total_price_qty = sum(p.get('quantity', 0) for p in price)
                price_quantity_distribution.append(total_price_qty)

                # Classify trade pattern
                if len(price) == 0:
                    trade_patterns['invalid'] += 1
                elif len(price) == 1:
                    if quantity == 1:
                        trade_patterns['single_item_qty_1'] += 1
                    else:
                        trade_patterns['single_item_bulk'] += 1
                        item_bulk_frequency[item_name] += 1
                else:
                    if quantity == 1 and all(p.get('quantity', 0) == 1 for p in price):
                        trade_patterns['multi_item_clean'] += 1
                    else:
                        trade_patterns['multi_item_bulk'] += 1
                        item_bulk_frequency[item_name] += 1

                # Flag suspicious trades
                suspicious_flags = []
                if quantity > 5:
                    suspicious_flags.append('high_offer_qty')
                if total_price_qty > 10:
                    suspicious_flags.append('high_ask_qty')
                if quantity * total_price_qty > 50:
                    suspicious_flags.append('extreme_volume')
                if len(price) > 3:
                    suspicious_flags.append('complex_bundle')

                if suspicious_flags:
                    suspicious_trades.append({
                        'item': item_name,
                        'quantity': quantity,
                        'price': price,
                        'total_price_qty': total_price_qty,
                        'flags': suspicious_flags,
                        'seller': seller,
                        'updated_at': updated_at
                    })

                # Track highest quantity trades
                if quantity > 10 or total_price_qty > 20:
                    highest_qty_trades.append({
                        'item': item_name,
                        'quantity': quantity,
                        'price': price,
                        'total_price_qty': total_price_qty,
                        'seller': seller,
                        'updated_at': updated_at
                    })

                # Calculate potential ratio distortion for single-item trades
                if len(price) == 1 and price[0].get('quantity', 0) > 0:
                    implied_ratio = quantity / price[0]['quantity']
                    if implied_ratio > 10 or implied_ratio < 0.1:
                        extreme_ratios.append({
                            'item_offered': item_name,
                            'item_asked': price[0]['name'],
                            'ratio': f"{quantity}:{price[0]['quantity']}",
                            'decimal_ratio': implied_ratio,
                            'seller': seller,
                            'updated_at': updated_at
                        })

    return {
        'server': server_name,
        'total_trades': total_trades,
        'trade_patterns': trade_patterns,
        'quantity_stats': {
            'min': min(quantity_distribution) if quantity_distribution else 0,
            'max': max(quantity_distribution) if quantity_distribution else 0,
            'avg': sum(quantity_distribution) / len(quantity_distribution) if quantity_distribution else 0,
            'distribution': Counter(quantity_distribution)
        },
        'price_quantity_stats': {
            'min': min(price_quantity_distribution) if price_quantity_distribution else 0,
            'max': max(price_quantity_distribution) if price_quantity_distribution else 0,
            'avg': sum(price_quantity_distribution) / len(
                price_quantity_distribution) if price_quantity_distribution else 0,
            'distribution': Counter(price_quantity_distribution)
        },
        'item_bulk_frequency': dict(item_bulk_frequency),
        'suspicious_trades': suspicious_trades,
        'highest_qty_trades': sorted(highest_qty_trades, key=lambda x: x['quantity'] + x['total_price_qty'],
                                     reverse=True)[:50],
        'extreme_ratios': sorted(extreme_ratios, key=lambda x: abs(x['decimal_ratio'] - 1), reverse=True)[:30]
    }


def generate_report(analysis_results):
    """Generate a comprehensive report from analysis results."""

    print("=" * 80)
    print("TRADERIE BULK DISTORTION ANALYSIS REPORT")
    print("=" * 80)
    print(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")

    # Summary across all servers
    total_all_trades = sum(r['total_trades'] for r in analysis_results)
    print(f"OVERALL SUMMARY")
    print(f"Total trades across all servers: {total_all_trades:,}")
    print()

    # Per-server breakdown
    for result in analysis_results:
        server = result['server']
        total = result['total_trades']
        patterns = result['trade_patterns']

        print(f"SERVER: {server.upper()}")
        print(f"Total trades: {total:,}")
        print()

        print("Trade Pattern Distribution:")
        for pattern, count in patterns.items():
            pct = (count / total * 100) if total > 0 else 0
            print(f"  {pattern:20}: {count:6,} ({pct:5.1f}%)")
        print()

        # Bulk distortion impact
        bulk_trades = patterns['single_item_bulk'] + patterns['multi_item_bulk']
        bulk_pct = (bulk_trades / total * 100) if total > 0 else 0
        print(f"BULK DISTORTION IMPACT:")
        print(f"  Potentially distorted trades: {bulk_trades:,} ({bulk_pct:.1f}%)")
        print()

        # Quantity statistics
        qty_stats = result['quantity_stats']
        print(f"Offer Quantity Distribution:")
        print(f"  Range: {qty_stats['min']} to {qty_stats['max']}")
        print(f"  Average: {qty_stats['avg']:.2f}")
        print("  Most common quantities:")
        for qty, count in sorted(qty_stats['distribution'].items())[:10]:
            print(f"    qty={qty}: {count:,} trades")
        print()

        # Price quantity statistics
        price_qty_stats = result['price_quantity_stats']
        print(f"Ask Quantity Distribution:")
        print(f"  Range: {price_qty_stats['min']} to {price_qty_stats['max']}")
        print(f"  Average: {price_qty_stats['avg']:.2f}")
        print()

        # Most bulk-affected items
        print("Items Most Affected by Bulk Trading:")
        bulk_items = sorted(result['item_bulk_frequency'].items(), key=lambda x: x[1], reverse=True)[:10]
        for item, count in bulk_items:
            print(f"  {item:25}: {count:3} bulk trades")
        print()

        # Extreme ratios
        print("Most Extreme Ratios (Potential Distortions):")
        for i, ratio in enumerate(result['extreme_ratios'][:10], 1):
            print(
                f"  {i:2}. {ratio['item_offered']} → {ratio['item_asked']}: {ratio['ratio']} (={ratio['decimal_ratio']:.2f})")
        print()

        # Highest quantity trades
        print("Highest Quantity Trades (Most Suspicious):")
        for i, trade in enumerate(result['highest_qty_trades'][:10], 1):
            price_items = [f"{p['name']}×{p['quantity']}" for p in trade['price']]
            price_str = " + ".join(price_items)
            print(f"  {i:2}. {trade['item']}×{trade['quantity']} → {price_str}")
            print(f"      Seller: {trade['seller']}, Updated: {trade['updated_at'][:10]}")
        print()

        print("-" * 80)
        print()


def save_detailed_analysis(analysis_results, output_dir):
    """Save detailed analysis to CSV files for further inspection."""

    if not os.path.exists(output_dir):
        os.makedirs(output_dir)

    # Combine suspicious trades from all servers
    all_suspicious = []
    all_extreme_ratios = []
    all_highest_qty = []

    for result in analysis_results:
        server = result['server']

        # Add server info to each record
        for trade in result['suspicious_trades']:
            trade['server'] = server
            all_suspicious.append(trade)

        for ratio in result['extreme_ratios']:
            ratio['server'] = server
            all_extreme_ratios.append(ratio)

        for trade in result['highest_qty_trades']:
            trade['server'] = server
            all_highest_qty.append(trade)

    # Save to CSV files
    if all_suspicious:
        df_suspicious = pd.DataFrame(all_suspicious)
        df_suspicious.to_csv(f"{output_dir}/suspicious_trades.csv", index=False)
        print(f"Saved {len(all_suspicious)} suspicious trades to suspicious_trades.csv")

    if all_extreme_ratios:
        df_ratios = pd.DataFrame(all_extreme_ratios)
        df_ratios.to_csv(f"{output_dir}/extreme_ratios.csv", index=False)
        print(f"Saved {len(all_extreme_ratios)} extreme ratios to extreme_ratios.csv")

    if all_highest_qty:
        df_qty = pd.DataFrame(all_highest_qty)
        df_qty.to_csv(f"{output_dir}/highest_qty_trades.csv", index=False)
        print(f"Saved {len(all_highest_qty)} high quantity trades to highest_qty_trades.csv")


def main():
    # Define file paths
    base_dir = "/"
    raw_data_dir = f"{base_dir}/data/raw"
    output_dir = f"{base_dir}/analysis"

    # Raw trade files
    trade_files = [
        ("pc_hc_l", f"{raw_data_dir}/raw_trades_pc_hc_l.json"),
        ("pc_hc_nl", f"{raw_data_dir}/raw_trades_pc_hc_nl.json"),
        ("pc_sc_l", f"{raw_data_dir}/raw_trades_pc_sc_l.json"),
        ("pc_sc_nl", f"{raw_data_dir}/raw_trades_pc_sc_nl.json")
    ]

    # Analyze each server
    analysis_results = []

    for server_name, file_path in trade_files:
        if os.path.exists(file_path):
            print(f"Analyzing {server_name}...")
            raw_data = load_raw_trades(file_path)
            if raw_data:
                result = analyze_trade_patterns(raw_data, server_name)
                analysis_results.append(result)
            else:
                print(f"No data found in {file_path}")
        else:
            print(f"File not found: {file_path}")

    if analysis_results:
        # Generate main report
        generate_report(analysis_results)

        # Save detailed analysis
        save_detailed_analysis(analysis_results, output_dir)

        print(f"\nDetailed analysis files saved to: {output_dir}/")
        print("Review the CSV files for manual inspection of suspicious trades.")
    else:
        print("No data to analyze. Check file paths and data availability.")


if __name__ == "__main__":
    main()