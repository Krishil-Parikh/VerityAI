import fs from 'fs';
import path from 'path';

export interface TelemetryData {
    time: string;
    temperature: number;
    altitude: number;
    voltage: number;
    latitude: number;
    longitude: number;
    acceleration: number;
    gyro: number;
}

export async function getTelemetryData(): Promise<TelemetryData[]> {
    try {
        // Construct path to the CSV file
        // Assuming the template folder is in the root of the project workspace
        const filePath = path.join(process.cwd(), 'template', 'ARYA_GUI-main', 'TableData.csv');

        if (!fs.existsSync(filePath)) {
            console.error(`CSV file not found at: ${filePath}`);
            return [];
        }

        const fileContent = fs.readFileSync(filePath, 'utf-8');
        const lines = fileContent.split('\n');

        // Skip header row
        const dataLines = lines.slice(1);

        const parsedData: TelemetryData[] = dataLines
            .filter(line => line.trim() !== '') // Filter out empty lines
            .map(line => {
                const columns = line.split(',');

                // CSV Structure based on header:
                // TEAM ID,MISSION TIME,PACKET_COUNT,MODE,TEMP,ALTITUDE,VOLTAGE,GNSS TIME,GNSS_LONGITUDE,GNSS_LATITUDE,ACCELERATION,GYRO_SPIN_RATE
                // 0        1            2            3    4    5        6       7         8              9             10           11

                if (columns.length < 12) return null;

                const parseValue = (val: string, itemsToRemove: string[]) => {
                    let cleaned = val;
                    itemsToRemove.forEach(item => {
                        cleaned = cleaned.replace(item, '');
                    });
                    return parseFloat(cleaned.trim());
                };

                return {
                    time: columns[1],
                    temperature: parseValue(columns[4], ['°C', 'C']),
                    altitude: parseValue(columns[5], ['m']),
                    voltage: parseValue(columns[6], ['V']),
                    longitude: parseFloat(columns[8]),
                    latitude: parseFloat(columns[9]),
                    acceleration: parseValue(columns[10], ['m/s^2']),
                    gyro: parseValue(columns[11], ['rpm'])
                };
            })
            .filter((item): item is TelemetryData => item !== null);

        return parsedData;

    } catch (error) {
        console.error('Error reading telemetry data:', error);
        return [];
    }
}
