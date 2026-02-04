"use client";

import React, { useEffect, useState } from 'react';
import {
    LineChart,
    Line,
    XAxis,
    YAxis,
    CartesianGrid,
    Tooltip,
    Legend,
    ResponsiveContainer,
    ScatterChart,
    Scatter,
    ZAxis
} from 'recharts';
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { TelemetryData } from '../lib/data';


export function GraphsDashboard() {
    const [data, setData] = useState<TelemetryData[]>([]);
    const [currentIndex, setCurrentIndex] = useState(0);

    useEffect(() => {
        const fetchData = async () => {
            try {
                const response = await fetch(`/api/telemetry?index=${currentIndex}`);
                if (response.ok) {
                    const newDataPoint = await response.json();
                    setData(prevData => [...prevData, newDataPoint]);
                    setCurrentIndex(prevIndex => prevIndex + 1);
                } else {
                    // Stop polling if we reach the end or error
                    console.log("Stream finished or error");
                }
            } catch (error) {
                console.error("Error fetching telemetry:", error);
            }
        };

        const intervalId = setInterval(fetchData, 1000); // Fetch every 1 second

        return () => clearInterval(intervalId);
    }, [currentIndex]); // Depend on currentIndex to fetch the next one

    return (
        <div className="space-y-6">
            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                {/* Voltage Chart */}
                <Card>
                    <CardHeader>
                        <CardTitle>Voltage</CardTitle>
                    </CardHeader>
                    <CardContent className="h-[300px]">
                        <ResponsiveContainer width="100%" height="100%">
                            <LineChart data={data}>
                                <CartesianGrid strokeDasharray="3 3" />
                                <XAxis dataKey="time" />
                                <YAxis unit="V" domain={['auto', 'auto']} />
                                <Tooltip />
                                <Legend />
                                <Line type="monotone" dataKey="voltage" stroke="#8884d8" strokeWidth={2} dot={false} isAnimationActive={false} />
                            </LineChart>
                        </ResponsiveContainer>
                    </CardContent>
                </Card>

                {/* Altitude Chart */}
                <Card>
                    <CardHeader>
                        <CardTitle>Altitude</CardTitle>
                    </CardHeader>
                    <CardContent className="h-[300px]">
                        <ResponsiveContainer width="100%" height="100%">
                            <LineChart data={data}>
                                <CartesianGrid strokeDasharray="3 3" />
                                <XAxis dataKey="time" />
                                <YAxis unit="m" domain={['auto', 'auto']} />
                                <Tooltip />
                                <Legend />
                                <Line type="monotone" dataKey="altitude" stroke="#82ca9d" strokeWidth={2} dot={false} isAnimationActive={false} />
                            </LineChart>
                        </ResponsiveContainer>
                    </CardContent>
                </Card>

                {/* Temperature Chart */}
                <Card>
                    <CardHeader>
                        <CardTitle>Temperature</CardTitle>
                    </CardHeader>
                    <CardContent className="h-[300px]">
                        <ResponsiveContainer width="100%" height="100%">
                            <LineChart data={data}>
                                <CartesianGrid strokeDasharray="3 3" />
                                <XAxis dataKey="time" />
                                <YAxis unit="°C" domain={['auto', 'auto']} />
                                <Tooltip />
                                <Legend />
                                <Line type="monotone" dataKey="temperature" stroke="#ffc658" strokeWidth={2} dot={false} isAnimationActive={false} />
                            </LineChart>
                        </ResponsiveContainer>
                    </CardContent>
                </Card>

                {/* Ground Track / trajectory (Lat/Long) */}
                <Card>
                    <CardHeader>
                        <CardTitle>Ground Track (GPS)</CardTitle>
                    </CardHeader>
                    <CardContent className="h-[300px]">
                        <ResponsiveContainer width="100%" height="100%">
                            <ScatterChart margin={{ top: 20, right: 20, bottom: 20, left: 20 }}>
                                <CartesianGrid />
                                <XAxis type="number" dataKey="longitude" name="Longitude" domain={['auto', 'auto']} />
                                <YAxis type="number" dataKey="latitude" name="Latitude" domain={['auto', 'auto']} />
                                <ZAxis type="number" dataKey="altitude" range={[0, 500]} name="Altitude" />
                                <Tooltip cursor={{ strokeDasharray: '3 3' }} />
                                <Scatter name="Path" data={data} fill="#ff7300" line isAnimationActive={false} />
                            </ScatterChart>
                        </ResponsiveContainer>
                    </CardContent>
                </Card>

                {/* Acceleration Chart */}
                <Card>
                    <CardHeader>
                        <CardTitle>Acceleration</CardTitle>
                    </CardHeader>
                    <CardContent className="h-[300px]">
                        <ResponsiveContainer width="100%" height="100%">
                            <LineChart data={data}>
                                <CartesianGrid strokeDasharray="3 3" />
                                <XAxis dataKey="time" />
                                <YAxis unit="m/s²" domain={['auto', 'auto']} />
                                <Tooltip />
                                <Legend />
                                <Line type="monotone" dataKey="acceleration" stroke="#ff0000" strokeWidth={2} dot={false} isAnimationActive={false} />
                            </LineChart>
                        </ResponsiveContainer>
                    </CardContent>
                </Card>
            </div>
        </div>
    );
}
