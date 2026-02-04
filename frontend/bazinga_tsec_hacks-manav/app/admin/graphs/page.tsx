import { GraphsDashboard } from './components/GraphsDashboard';

export default function GraphsPage() {
    return (
        <div className="p-6">
            <h1 className="text-3xl font-bold mb-6">Telemetry Graphs</h1>
            <GraphsDashboard />
        </div>
    );
}
