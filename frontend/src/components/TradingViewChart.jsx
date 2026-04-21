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
        const formattedData = data.map(item => {
            let timeValue = item.date || item.time || (item.timestamp ? item.timestamp / 1000 : null);
            
            // Handle ISO strings (e.g., 2026-03-08T14:58:53.859382)
            if (typeof timeValue === 'string') {
                if (timeValue.includes('T')) {
                    timeValue = timeValue.split('T')[0];
                } else if (timeValue.includes(' ')) {
                    // Handle "2026-03-08 14:58:53"
                    timeValue = timeValue.split(' ')[0];
                }
            }
            
            // Final fallback to numeric timestamp if still not a simple YYYY-MM-DD
            // lightweight-charts prefers numbers for intra-day and YYYY-MM-DD for daily
            if (typeof timeValue === 'string' && !/^\d{4}-\d{2}-\d{2}$/.test(timeValue)) {
                // If it's not YYYY-MM-DD, try to convert to unix timestamp
                const d = new Date(timeValue);
                if (!isNaN(d.getTime())) {
                    timeValue = Math.floor(d.getTime() / 1000);
                }
            }

            return {
                time: timeValue,
                open: parseFloat(item.open || item.price),
                high: parseFloat(item.high || item.price),
                low: parseFloat(item.low || item.price),
                close: parseFloat(item.close || item.price),
            };
        }).filter(item => item.time !== null && !isNaN(item.open))
        .sort((a, b) => {
            const timeA = typeof a.time === 'string' ? new Date(a.time).getTime() : a.time * 1000;
            const timeB = typeof b.time === 'string' ? new Date(b.time).getTime() : b.time * 1000;
            return timeA - timeB;
        });

        if (formattedData.length > 0) {
            candlestickSeries.setData(formattedData);
        }

        // Add volume if available
        if (data[0] && data[0].volume !== undefined) {
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

            const volumeData = data.map((item, idx) => {
                const fItem = formattedData[idx];
                if (!fItem) return null;
                return {
                    time: fItem.time,
                    value: parseFloat(item.volume),
                    color: parseFloat(item.close || item.price) >= parseFloat(item.open || item.price) ? 'rgba(38, 166, 154, 0.5)' : 'rgba(239, 83, 80, 0.5)',
                };
            }).filter(Boolean);

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
