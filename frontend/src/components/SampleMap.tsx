import React from 'react';

type Props = {
  latitude: number | null;
  longitude: number | null;
  latitude_end: number | null;
  longitude_end: number | null;
};

const SampleMap = ({ latitude, longitude, latitude_end, longitude_end }: Props) => {
  const hasLocationData =
    latitude !== null &&
    longitude !== null;

  return (
    <div className="bg-blue-500 h-50 flex flex-col justify-center items-center p-4 text-white rounded-sm">
        <p>Sample Map</p>
      {hasLocationData ? (
        <>
          <p>Start: ({latitude}, {longitude})</p>
          <p>End: ({latitude_end}, {longitude_end})</p>
        </>
      ) : (
        <p>No location data</p>
      )}
    </div>
  );
};

export default SampleMap;
