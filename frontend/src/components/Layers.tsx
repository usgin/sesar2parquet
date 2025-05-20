import TileLayer from 'ol/layer/Tile';
import VectorTileLayer from 'ol/layer/VectorTile';
import VectorLayer from 'ol/layer/Vector';
import LayerGroup from 'ol/layer/Group';
import OSM from 'ol/source/OSM';
import TileWMS from 'ol/source/TileWMS';
import XYZ from 'ol/source/XYZ';
import VectorTileSource from 'ol/source/VectorTile';
import { Style, Fill, Stroke } from 'ol/style';
import MVT from 'ol/format/MVT';
import VectorSource from 'ol/source/Vector';

type LayerType =
    | TileLayer
    | VectorTileLayer
    | VectorLayer
    | LayerGroup;

type LayerKey =
    | 'osm'
    | 'gmrtMercator'
    | 'gmrtNorth'
    | 'gmrtSouth'
    | 'macrostratVector'
    | 'macrostratPNG'
    | 'drawLayer'
    | 'baseGroup';

export function createLayers(
    vectorSource: VectorSource,
    options: { include?: LayerKey[] } = {}
): LayerType[] {
    const layersMap: Record<LayerKey, LayerType> = {
    osm: new TileLayer({
        source: new OSM(),
        visible: false,
    }),
    gmrtMercator: new TileLayer({
        source: new TileWMS({
        url: 'https://www.gmrt.org/services/mapserv/wms_merc?',
        params: { LAYERS: 'topo', format: 'jpeg', SRS: 'EPSG:4326' },
        serverType: 'geoserver',
        }),
        visible: true,
    }),
    gmrtNorth: new TileLayer({
        source: new TileWMS({
        url: 'https://www.gmrt.org/services/mapserv/wms_NP?',
        params: {
            LAYERS: 'North_Polar_Bathymetry',
            format: 'jpeg',
            SRS: 'EPSG:3995',
        },
        serverType: 'geoserver',
        }),
        visible: false,
    }),
    gmrtSouth: new TileLayer({
        source: new TileWMS({
        url: 'https://www.gmrt.org/services/mapserv/wms_SP?',
        params: {
            LAYERS: 'South_Polar_Bathymetry',
            format: 'jpeg',
            SRS: 'EPSG:3031',
        },
        serverType: 'geoserver',
        }),
        visible: false,
    }),
    macrostratVector: new VectorTileLayer({
        source: new VectorTileSource({
        format: new MVT(),
        url: 'https://tiles.macrostrat.org/carto/{z}/{x}/{y}.mvt',
        }),
        visible: false,
        style: feature => {
        const color = feature.get('color');
        return new Style({
            fill: new Fill({ color: color || 'rgba(255,255,255,0)' }),
            stroke: new Stroke({ color: 'rgba(0,0,0,0.2)', width: 1 }),
        });
        },
    }),
    macrostratPNG: new TileLayer({
        source: new XYZ({
        url: 'https://tiles.macrostrat.org/carto/{z}/{x}/{y}.png',
        }),
        visible: false,
    }),
    drawLayer: new VectorLayer({
        source: vectorSource,
        style: new Style({
        fill: new Fill({ color: 'rgba(255, 255, 255, 0.2)' }),
        stroke: new Stroke({ color: '#3333ff', width: 2 }),
        }),
    }),
    baseGroup: new LayerGroup({ layers: [] }),
    };

    layersMap.osm.set('title', 'OSM');
    layersMap.osm.set('type', 'base');

    layersMap.gmrtMercator.set('title', 'GMRT Bathymetry');
    layersMap.gmrtMercator.set('type', 'base');

    layersMap.gmrtNorth.set('title', 'GMRT North Polar Bathymetry');
    layersMap.gmrtNorth.set('type', 'base');
    layersMap.gmrtNorth.set('displayInLayerSwitcher', false);

    layersMap.gmrtSouth.set('title', 'GMRT South Polar Bathymetry');
    layersMap.gmrtSouth.set('type', 'base');
    layersMap.gmrtSouth.set('displayInLayerSwitcher', false);

    layersMap.macrostratVector.set('title', 'MacroStrat');
    layersMap.macrostratVector.set('displayInLayerSwitcher', true);
    layersMap.macrostratVector.set('isMercator', true);

    layersMap.macrostratPNG.set('title', 'MacroStrat PNG');
    layersMap.macrostratPNG.set('displayInLayerSwitcher', false);
    layersMap.macrostratPNG.set('isMercator', false);

    layersMap.drawLayer.set('title', 'Draw Layer');
    layersMap.drawLayer.set('displayInLayerSwitcher', false);

    const baseGroup = new LayerGroup({ layers: [] });
    baseGroup.getLayers().push(layersMap.osm);
    baseGroup.getLayers().push(layersMap.gmrtMercator);
    baseGroup.set('title', 'Base Layers');
    layersMap.baseGroup = baseGroup;

    // Return selected layers or all layers as array
    if (!options.include) {
    return Object.values(layersMap);
    }

    return options.include.map(key => layersMap[key]);
}
