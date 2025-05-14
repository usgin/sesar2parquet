import React from 'react';
import { Metadata } from 'next';
import LandingPageDataTable from "@/components/LandingPageDataTable";
import ImageGallery from "@/components/ImageGallery";
import SampleMap from "@/components/SampleMap";
import SampleFamily from "@/components/SampleFamily"
import SamplePublication from "@/components/SamplePublication"

type Props = {
  params: {
    igsn: string[]
  }
};


export async function generateMetadata({ params }: Props): Promise<Metadata> {
    const {igsn} = await params;
    const igsn_value = igsn.join('/');
    return {
        title: `SESAR: ${igsn_value}`,
        description: `Sample Landing Page for IGSN ${igsn_value}`,
    };
}


const SampleLandingPage = async ({ params }: Props) => {
  const {igsn} = await params;
  const igsn_value = igsn.join('/');

  const baseUrl = process.env.NEXT_PUBLIC_API2_BASE_URL;
  const res = await fetch(`${baseUrl}/api/samples/?igsn=${igsn_value}`, {
    cache: 'no-store',
  });

  if (!res.ok) {
    // You might want to handle 404s, etc.
    return <div>Error loading sample data</div>;
  }

  const oldUrl = process.env.NEXT_PUBLIC_API_BASE_URL;
  const oldRes = await fetch(`${oldUrl}/api/samples/?igsn=${igsn_value}`, {
    cache: 'no-store',
  });

  const sample = await res.json();

  const original = await oldRes.json();

  const latitude = sample.latitude; 
  const longitude = sample.longitude;
  const latitudeEnd = sample.latitude_end;
  const longitudeEnd = sample.longitude_end;

  const general = {
    'IGSN': {
      value: sample.igsn,
      original: original.igsn,
    },
    'Name': {
      value: sample.name,
      original: original.name,
    },
    'Other Name(s)': {
      value: sample.other_names.join(', '),
      original: [
        ...(original.other_names ?? []),
        ...(original.external_sample_id ? [original.external_sample_id] : [])
      ].join(', ')
    },
    'Publish Date': {
      value: sample.publish_date?.slice(0, 10) ?? null,
      original: original.publish_date?.slice(0, 10) ?? null,
    },
    'Last Updated': {
      value: sample.last_update_date?.slice(0, 10) ?? null,
      original: original.last_update_date?.slice(0, 10) ?? null,
    },
  };

  const description = {
    'Material Type': {
      value: sample.general_material_type?.label ?? null,
      original: original.top_level_classification,
    },
    'Object Type': {
      value: sample.sample_type,
      original: original.sample_type,
    },
    'Classification': {
      value: [...sample.sample_material]
      .map(item => item.label)
      .filter(label => label)
      .join(', '),
      original: original.classification,
    },
    'Other Classification': {
      value: sample.material_name_verbatim,
      original: [
        ...(original.sample_type ? [original.sample_type] : []),
        ...(original.top_level_classification ? [original.top_level_classification] : []),
        ...(original.classification ? [original.classification] : []),
        ...(original.field_name ? [original.field_name] : []),
      ].join(', '),
    },
    'Sample Description': {
      value: sample.sample_description,
      original: [
        ...(original.description ? [original.description] : []),
        ...(original.classification_comment ? [original.classification_comment] : []),
        ...(original.sample_comment ? [original.sample_comment] : []),
        ...(original.collector_detail ? [original.collector_detail] : []),
      ].join(', '),
    },
    'Age (min)': {
      value: sample.numeric_age_min,
      original: original.age_min,
    },
    'Age (max)': {
      value: sample.numeric_age_max,
      original: original.age_max,
    },
    'Age Unit': {
      value: sample.numeric_age_unit,
      original: original.age_unit,
    },
    'Sample Size': {
      value: sample.size,
      original: original.size,
    },
    'Geological Age': {
      value: sample.geologic_age_verbatim,
      original: [
        ...(original.geologic_age ? [original.geologic_age] : []),
        ...(original.age_min ? [original.age_min] : []),
        ...(original.age_max ? [original.age_max] : []),
        ...(original.age_unit ? [original.age_unit] : []),
      ].join(', '),
    },
    'Geological Unit': {
      value: sample.geologic_unit,
      original: original.geological_unit,
    },
    'Purpose': {
      value: sample.purpose,
      original: original.purpose,
    }
  };

  const location = {
    'Latitude': {
      value: sample.latitude,
      original: original.latitude,
    },
    'Latitude End': {
      value: sample.latitude_end,
      original: original.latitude_end,
    },
    'Longitude': {
      value: sample.longitude,
      original: original.longitude,
    },
    'Longitude End': {
      value: sample.longitude_end,
      original: original.longitude_end,
    },
    'Vertical Datum': {
      value: "TODO",
      original: original.vertical_datum,
    },
    'Depth (min)': {
      value: sample.depth_min,
      original: original.depth_min,
    },
    'Depth (max)': {
      value: sample.depth_max,
      original: original.depth_max,
    },
    'Depth Scale': {
      value: sample.depth_uom,
      original: original.depth_scale,
    },
    'Elevation': {
      value: sample.elevation,
      original: [
        ...(original.elevation ? [original.elevation] : []),
        ...(original.elevation_end ? [original.elevation_end] : []),
      ].join(', '),
    },
    'Nav Type': {
      value: sample.location_method?.label ?? null,
      original: original.nav_type,
    },
    'Location Name': {
      value: sample.locality?.name,
      original: [
        ...(original.locality ? [original.locality] : []),
        ...(original.primary_location_type ? [original.primary_location_type] : []),
        ...(original.province ? [original.province] : []),
        ...(original.county ? [original.county] : []),
        ...(original.city ? [original.city] : []),
      ].join(', '),
    },
    'Locality Description': {
      value: sample.locality_detail,
      original: [
        ...(original.primary_location_name ? [original.primary_location_name] : []),
        ...(original.primary_location_type ? [original.primary_location_type] : []),
        ...(original.location_description ? [original.location_description] : []),
        ...(original.locality ? [original.locality] : []),
        ...(original.locality_description ? [original.locality_description] : []),
        ...(original.country ? [original.country] : []),
        ...(original.province ? [original.province] : []),
        ...(original.county ? [original.county] : []),
        ...(original.city ? [original.city] : []),
      ].join(', '),
    }
  }

  const curation = {
    'Current Archive': {
      value: [...sample.current_archive]
      .map(item => item.label)
      .filter(label => label) // remove null/undefined/empty
      .join(', '),
      original: original.current_archive,
    },
    'Original Archive': {
      value:  [...sample.original_archive]
      .map(item => item.label)
      .filter(label => label) // remove null/undefined/empty
      .join(', '),
      original: original.original_archive,
    },
    'Registration Date': {
      value: sample.registration_date?.slice(0, 10) ?? null,
      original: original.registration_date?.slice(0, 10) ??null,
    },
    'Related Resources ': {
      value: [...sample.related_resources]
      .map(item => item.relation_label)
      .filter(relation_label => relation_label) // remove null/undefined/empty
      .join(', '),
      original: [
        ...(original.external_parent_name ? [original.external_parent_name] : []),
        ...(original.external_parent_sample_type ? [original.external_parent_sample_type] : []),
      ].join(', ')
    },
  }

  const collection = {
    'Cruise/Field Program': {
      value: sample.cruise_field_prgrm?.label ?? null,
      original: original.cruise_field_prgrm,
    },
    'Platform Name': {
      value: sample.platform?.label ?? null,
      original: original.platform_name,
    },
    'Platform Type': {
      value: sample.platform?.platform_type ?? null,
      original: original.platform_type,
    },
    'Launch Label': {
      value: sample.launch_platform?.label ?? null,
      original: original.launch_id,
    },
    'Launch Platform': {
      value: sample.launch_platform?.platform_type ?? null,
      original: original.launch_platform_name,
    },
    'Launch Type': {
      value: sample.launch_platform?.launch_type ?? null,
      original: original.launch_type,
    },
    'Collector': {
      value: [...sample.individual_collector, ...sample.institution_collector]
      .map(item => item.label)
      .filter(label => label) // remove null/undefined/empty
      .join(', '),
      original: original.collector,
    },
    'Collection Method': {
      value: sample.collection_method?.label ?? null,
      original: original.collection_method,
    },
    'Collection Start Date': {
      value: sample.collection_start_date?.slice(0, 10) ?? null,
      original: original.collection_start_date?.slice(0, 10) ?? null,
    },
    'Collection End Date': {
      value: sample.collection_end_date?.slice(0, 10) ?? null,
      original: original.collection_end_date?.slice(0, 10) ?? null,
    },
    'Collection Date Precision': {
      value: sample.collection_date_precision,
      original: original.collection_date_precision,
    }
  }

  const sample_parent = sample.parent_sample
  const sample_siblings = sample.sibling_igsns
  const sample_children = sample.children_igsns
  // const sample_publication_urls = sample.publication_urls

  return (
    <div className="flex flex-col md:flex-row h-screen">
      {/* Left Column */}
      <div className="w-full md:w-1/2 p-4 flex flex-col gap-4">
        <LandingPageDataTable title="General Identifiers" data={general}/>
        <LandingPageDataTable title="Description" data={description}/>
        <LandingPageDataTable title="Sampling Location" data={location}/>
        <LandingPageDataTable title="Curation" data={curation}/>
        <LandingPageDataTable title="Collection" data={collection}/>
      </div>

      {/* Right Column */}
      <div className="w-full md:w-1/2 p-4 flex flex-col gap-6">
        <SampleMap latitude={latitude} longitude={longitude} latitude_end={latitudeEnd} longitude_end={longitudeEnd}/>
        <ImageGallery />
        <SampleFamily parent_igsn={sample_parent} sibling_igsns={sample_siblings} children_igsns={sample_children}/>
        <SamplePublication links={sample.publication_urls}/>
      </div>
    </div>
  );
};

export default SampleLandingPage;
