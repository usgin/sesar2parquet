import React from 'react';
import { Metadata } from 'next';
import LandingPageDataTable from "@/components/LandingPageDataTable";
import ImageGallery from "@/components/ImageGallery";
import SampleMap from "@/components/SampleMap";
import SampleFamily from "@/components/SampleFamily"
import SamplePublication from "@/components/SamplePublication"

export async function generateMetadata({ params }: { params: { igsn: string[] } }): Promise<Metadata> {
    const {igsn} = await params;
    let igsn_value = igsn.join('/');
    return {
        title: `SESAR: ${igsn_value}`,
        description: `Sample Landing Page for IGSN ${igsn_value}`,
    };
}
const sampleData = {
  Name: 'John Doe',
  Age: 30,
  Occupation: 'Engineer',
  Member: true,
};

const SampleLandingPage = async ({ params }: { params: { igsn: string[] } }) => {
  const {igsn} = await params;
  let igsn_value = igsn.join('/');

  return (
    <div className="flex flex-col md:flex-row h-screen">
      {/* Left Column */}
      <div className="w-full md:w-1/2 p-4 flex flex-col gap-4">
        <LandingPageDataTable title="General Identifiers" data={sampleData}/>
        <LandingPageDataTable title="Sampling Location" data={sampleData}/>
        <LandingPageDataTable title="Description" data={sampleData}/>
        <LandingPageDataTable title="Curation" data={sampleData}/>
        <LandingPageDataTable title="Collection" data={sampleData}/>
      </div>

      {/* Right Column */}
      <div className="w-full md:w-1/2 p-4 bg-gray-200 flex flex-col gap-6">
        <SampleMap latitude={5} longitude={6} latitude_end={6} longitude_end={6}/>
        <ImageGallery />
        <SampleFamily />
        <SamplePublication />
      </div>

      {/* Display IGSN */}
      {/* <h1 className="text-3xl">IGSN: {igsn_value}</h1> */}
    </div>
  );
};

export default SampleLandingPage;
