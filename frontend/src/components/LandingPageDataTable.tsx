import React from 'react'

type DataDisplayProps = {
    title: string;
    data: Record<string, string | number | boolean>;
  };

const LandingPageDataTable = ({ title, data }: DataDisplayProps) => {
    return (
        <div className="flex flex-col">
            <h2 className="text-xl font-bold bg-cyan-700 rounded-t-sm text-white pl-1">{title}</h2>
            {Object.entries(data).map(([key, value]) => (
                <div key={key} className="flex odd:bg-gray-200">
                    <div className="w-1/2 p-1 font-bold pr-4">{key}</div>
                    <div className="w-1/2 p-1 pl-4">{value}</div>
                </div>
            ))}
        </div>
    );
}

export default LandingPageDataTable