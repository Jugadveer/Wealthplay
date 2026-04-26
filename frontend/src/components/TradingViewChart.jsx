import React, { useEffect, useRef } from 'react';
import { createChart, ColorType } from 'lightweight-charts';

const TradingViewChart = ({ data, colors = {} }) => {
    const chartContainerRef = useRef();

    useEffect(() => {
        if (!data || data.length === 0) return;

        const handleResize = () => {
            chart.applyOptions({ width: chartContainerRef.current.clientWidth });
        };

        const chart = createChart(chartContainerRef.current, {
            layout: {
                background: { type: ColorType.Solid, color: colors.background || 'transparent' },
                textColor: colors.textColor || '#444',
            },
            width: chartContainerRef.current.clientWidth,
            height: 300,
            grid: {
                vertLines: { color: 'rgba(197, 203, 206, 0.2)' },
                horzLines: { color: 'rgba(197, 203, 206, 0.2)' },
            },
            timeScale: {
                borderColor: 'rgba(197, 203, 206, 0.4)',
                timeVisible: true,
                secondsVisible: false,
            },
        });

        const candlestickSeries = chart.addCandlestickSeries({
            upColor: '#26a69a',
            downColor: '#ef5350',
            borderVisible: false,
            wickUpColor: '#26a69a',
            wickDownColor: '#ef5350',
        });

        // Format data for lightweight-charts
        const formattedDataMap = new Map();
        
        data.forEach(item => {
            let originalTime = item.date || item.time || item.timestamp;
            if (!originalTime) return;

            let timeValue;
            let dateObj;

            // Robust parsing for different timestamp/date formats
            if (typeof originalTime === 'number') {
                // If it's a number, check if it's seconds or milliseconds
                // Milliseconds are usually > 10^12 (year 2001+)
                dateObj = new Date(originalTime > 1e11 ? originalTime : originalTime * 1000);
            } else {
                dateObj = new Date(originalTime);
            }
            
            if (isNaN(dateObj.getTime())) return;

            // Consistency Fix: Always use Unix Timestamps (seconds) for all data points.
            // This prevents "isUTCTimestamp" errors caused by mixing formats.
            timeValue = Math.floor(dateObj.getTime() / 1000);

            // Deduplicate by time to satisfy library ordering/uniqueness requirements
            formattedDataMap.set(timeValue, {
                time: timeValue,
                open: parseFloat(item.open || item.price || 0),
                high: parseFloat(item.high || item.price || 0),
                low: parseFloat(item.low || item.price || 0),
                close: parseFloat(item.close || item.price || 0),
                volume: parseFloat(item.volume || 0),
            });
        });

        const formattedData = Array.from(formattedDataMap.values())
            .sort((a, b) => a.time - b.time);

        if (formattedData.length > 0) {
            candlestickSeries.setData(formattedData);
        }

        // Add volume if available
        const hasVolume = formattedData.some(item => item.volume > 0);
        if (hasVolume) {
            const volumeSeries = chart.addHistogramSeries({
                color: '#26a69a',
                priceFormat: {
                    type: 'volume',
                },
                priceScaleId: '', // set as an overlay
            });
            
            volumeSeries.priceScale().applyOptions({
                scaleMargins: {
                    top: 0.8, // highest point of the series will be 80% from top
                    bottom: 0,
                },
            });

            const volumeData = formattedData.map((fItem) => {
                return {
                    time: fItem.time,
                    value: fItem.volume,
                    color: fItem.close >= fItem.open ? 'rgba(38, 166, 154, 0.5)' : 'rgba(239, 83, 80, 0.5)',
                };
            });

            volumeSeries.setData(volumeData);
        }
    
        // To fix the "empty left side", we fit content
        chart.timeScale().fitContent();

        window.addEventListener('resize', handleResize);

        return () => {
            window.removeEventListener('resize', handleResize);
            chart.remove();
        };
    }, [data, colors]);

    return <div ref={chartContainerRef} className="w-full h-full" />;
};

export default TradingViewChart;
