'use client';

import React, { useEffect, useRef } from 'react';
import 'ol/ol.css';
import 'ol-layerswitcher/dist/ol-layerswitcher.css';
import Map from 'ol/Map';
import View from 'ol/View';
import VectorLayer from 'ol/layer/Vector';
import VectorSource from 'ol/source/Vector';
import Feature from 'ol/Feature';
import Point from 'ol/geom/Point';
import LineString from 'ol/geom/LineString';
import { fromLonLat } from 'ol/proj';
import { Style, Stroke, Circle, Fill } from 'ol/style';
import FullScreen from 'ol/control/FullScreen';
import { defaults as defaultControls } from 'ol/control/defaults';
import { createLayers } from './Layers';

export type Props = {
  latitude: number;
  latitudeEnd: number;
  longitude: number;
  longitudeEnd: number;
  zoom?: number;
};

const SampleMap = ({
  latitude,
  longitude,
  latitudeEnd,
  longitudeEnd,
  zoom = 4,
}: Props) => {
  const mapRef = useRef<HTMLDivElement | null>(null);
  const mapInstanceRef = useRef<Map | null>(null);

  useEffect(() => {
    if (!mapRef.current) return;

    const vectorSource = new VectorSource();
    const layers = createLayers(vectorSource, {
      include: ['baseGroup', 'macrostratVector'],
    });
    
    const center = fromLonLat([longitude, latitude]);
    const sampleStart = fromLonLat([longitude, latitude]);

    let sampleFeature;
    if (latitudeEnd && longitudeEnd) {
      const sampleEnd = fromLonLat([longitudeEnd, latitudeEnd]);
      sampleFeature = new Feature({
        geometry: new LineString([sampleStart, sampleEnd]),
      });
      sampleFeature.setStyle(
        new Style({
          stroke: new Stroke({
            color: 'blue',
            width: 5,
          }),
        }),
      );
    } else {
      sampleFeature = new Feature({
        geometry: new Point(sampleStart),
      });
      sampleFeature.setStyle(
        new Style({
          image: new Circle({
            radius: 5,
            fill: new Fill({ color: 'blue' }),
            stroke: new Stroke({ color: 'white', width: 2 }),
          }),
        }),
      );
    }

    const vectorLayer = new VectorLayer({
      source: new VectorSource({
        features: [sampleFeature],
      }),
    });

    const map = new Map({
      target: mapRef.current,
      controls: defaultControls().extend([new FullScreen()]),
      layers: [...layers, vectorLayer],
      view: new View({ center, zoom }),
    });

    mapInstanceRef.current = map;

    // Load layer switcher dynamically
    import('ol-layerswitcher').then(({ default: LayerSwitcher }) => {
      const layerSwitcher = new LayerSwitcher({
        reverse: true,
        groupSelectStyle: 'group',
      });
      map.addControl(layerSwitcher);
    });

    return () => {
      map.setTarget(undefined);
      mapInstanceRef.current = null;
    };
  }, [latitude, longitude, latitudeEnd, longitudeEnd, zoom]);

  return <div ref={mapRef} style={{ height: '400px' }} />;
};

export default SampleMap;
