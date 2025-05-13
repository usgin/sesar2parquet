import React from 'react';

type FieldData = {
  original: string | number | boolean | null;
  value: string | number | boolean | null;
};

type DataDisplayProps = {
  title: string;
  data: Record<string, FieldData>;
};

const LandingPageDataTable = ({ title, data }: DataDisplayProps) => {
  return (
    <div className="flex flex-col">
      <h2 className="text-xl font-bold bg-cyan-700 rounded-t-sm text-white pl-3">{title}</h2>
      <div className="flex font-bold bg-gray-300">
        <div className="w-1/3 p-1 pl-3  ">Field</div>
        <div className="w-1/3 p-1">Current Value</div>
        <div className="w-1/3 p-1">Original Value</div>
      </div>
      {Object.entries(data).map(([key, fieldData]) => (
        <div key={key} className="flex odd:bg-gray-100 even:bg-white">
          <div className="w-1/3 p-1 pl-3   font-semibold">{key}</div>
          <div className="w-1/3 p-1">{fieldData.value !== null && fieldData.value !== '' ? String(fieldData.value) : 'Not Provided'}</div>
          <div className="w-1/3 p-1 text-gray-600">{fieldData.original !== null && fieldData.original !== '' ? String(fieldData.original) : 'Not Provided'}</div>
        </div>
      ))}
    </div>
  );
};

export default LandingPageDataTable;
