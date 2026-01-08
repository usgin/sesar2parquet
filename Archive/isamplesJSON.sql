SELECT 
    json_build_object(
        '$schema', '../src/schemas/iSamplesSchemaCore2.0.json',
        'pid', CONCAT('sesar.', s.sample_id::text),
        'sample_identifier', s.igsn,
        'label', s.name,
        'description', CONCAT_WS('; ',
                    CASE WHEN s.sample_description IS NOT NULL THEN 'Sample description: ' || s.sample_description END,
                    CASE WHEN s.material_name_verbatim IS NOT NULL THEN 'Material verbatim: ' || s.material_name_verbatim END,
                    CASE WHEN s.geologic_age_verbatim IS NOT NULL THEN 'Age verbatim: ' || s.geologic_age_verbatim END,
                    CASE WHEN s.numeric_age_min IS NOT NULL THEN 'Age min: ' || s.numeric_age_min::TEXT END,
                    CASE WHEN s.numeric_age_max IS NOT NULL THEN 'Age max: ' || s.numeric_age_max::TEXT END,
                    CASE WHEN s.numeric_age_unit IS NOT NULL THEN 'Age units: ' || s.numeric_age_unit END
                ),
        'alternate_identifiers', (
                SELECT json_agg(
                     CONCAT(san.name_authority,'.',san.name)
                )
                FROM sample_additional_name san
                WHERE san.sample_id = s.sample_id
            ),
        'produced_by',
            json_build_object(
                'pid', CONCAT('event.', s.sample_id::text),
                'label', 'sampling event',
                'description', CONCAT_WS('; ',
                      CASE WHEN cm.label IS NOT NULL THEN 'Collection method: ' || cm.label END,
                      CASE WHEN length(s.collection_method_detail) > 1  THEN 'Method detail: '
                            || trim(both ' .' FROM split_part(s.collection_method_detail, 'Legacy collector:', 1)) END,
                      CASE WHEN p.label IS NOT NULL THEN 'Platform: ' || p.label END,
                      CASE WHEN lp.label IS NOT NULL THEN 'Launch platform: ' || lp.label END,
                      CASE WHEN s.launch_label IS NOT NULL THEN 'Launch: ' || s.launch_label END) ,
                'has_feature_of_interest', s.primary_location_type,
                'project', cfi.label,
                'responsibility', jsonb_build_object(
                    'name', CASE WHEN POSITION('Legacy collector' IN s.collection_method_detail) > 0
                                THEN trim(both ' .' FROM split_part(s.collection_method_detail, 'Legacy collector:', 2))
                                END,
                    'role', CASE WHEN POSITION('Legacy collector' IN s.collection_method_detail) > 0
                                THEN 'collector'  END
                    ),
                'result_time', s.collection_end_date,
                'sample_location', jsonb_build_object(
                    'elevation', concat(s.elevation, ' ', s.elevation_unit),
                    'latitude', s.latitude,
                    'longitude', s.longitude,
                    'obfuscated', FALSE
                ),
                'sampling_site', jsonb_build_object(
                        'description', CONCAT_WS('; ',
                            CASE WHEN s.locality_description IS NOT NULL THEN 'Locality: '
                                                        || s.locality_description END,
                            CASE WHEN s.location_description IS NOT NULL THEN 'Location: '
                                                        || s.location_description END,
                            CASE WHEN s.depth_min IS NOT NULL THEN 'Depth_min: '
                                                        || s.depth_min END,
                            CASE WHEN s.depth_min IS NOT NULL THEN 'Depth_min: '
                                                        || s.depth_min END,
                            CASE WHEN s.depth_max IS NOT NULL THEN 'Depth_max: '
                                                        || s.depth_max END,
                            CASE WHEN s.depth_scale IS NOT NULL THEN 'Depth_scale: '
                                                        || s.depth_scale END,
                            CASE WHEN s.vertical_datum IS NOT NULL THEN 'Vertical_datum: '
                                                        || s.vertical_datum END
                                       ),
                        'place_name', jsonb_build_array(
											s.primary_location_name,
                                               s.city,
                                               s.county,
                                               s.province,
                                                cty.label,
                                                cnt.label
										)
                )
            ),
    'sampling_purpose', s.purpose,
    'has_context_category', json_agg(
        jsonb_build_object(
            'label', 'missing',
            'pid', 'http://www.opengis.net/def/nil/OGC/0/missing',
            'scheme_name', 'OGC nil values'
        )
    ),
    'has_material_category', json_build_array(
                    jsonb_build_object(
                            'label', gmt.label,
                            'pid', gmt.material_type_uri,
                            'scheme_name', gmt.scheme_uri
                    ),
                     jsonb_build_object(
                            'label', lc.label,
                            'pid', lc.material_type_uri,
                            'scheme_name', lc.scheme_uri
                    )
          ),
    'has_sample_object_type', json_agg(
                    jsonb_build_object(
                            'label',st.label,
                            'pid', st.uri,
                            'scheme_name', st.scheme_name
                    )
            ),
    'keywords',json_build_array(
                jsonb_build_object(
                    'label', gay.label,
                    'pid', gay.geologic_time_interval_uri,
                    'scheme_uri', gay.scheme_uri
                ),
               jsonb_build_object(
                    'label', gao.label,
                    'pid', gao.geologic_time_interval_uri,
                    'scheme_uri', gao.scheme_uri
                )
    ),
    'related_resource',	(SELECT json_agg(json_build_object(
                'label', rres.label,
				'relationship', 'repository file',
				'target', rres.uri
            ))
           FROM related_resource_connection rc LEFT JOIN related_resource rres
		   		on rc.related_resource_id = rres.id
				   WHERE s.sample_id = rc.sample_id
                ),
	'curation', jsonb_build_object(
				'access_constraints', json_agg('not specified'::TEXT),
				'curation_location', (
					SELECT
						data -> 'archival_information' ->> 'current_archive' AS current_archive
					FROM sample_source_record ssr
					WHERE ssr.sample_id = s.sample_id
				),
				'responsibility', (SELECT json_agg(
					jsonb_build_object(
						'name', ind.label,
						'contact_information', ind.email,
						'pid', CASE
							   WHEN ind.individual_uri IS NOT NULL THEN 'orcid: '
								   || ind.individual_uri END,
						'role','owner'
						))
						FROM individual ind
						WHERE co.individual_id = ind.individual_id
				)
				),
	'last_modified_time','2025-10-19T06:00:00-07:00',
	'registrant', (SELECT jsonb_build_object(
		'name', ind.label,
		'contact_information', ind.email,
		'pid', CASE
			   WHEN ind.individual_uri IS NOT NULL THEN 'orcid: '
				   || ind.individual_uri END
		)
		FROM individual ind
		WHERE cr.individual_id = ind.individual_id
        )
    ) as isample_json
From
     sample s
    LEFT JOIN material_type gmt ON s.general_material_type_id = gmt.material_type_id
    Left join material_type lc on s.legacy_classification_id = lc.material_type_id
    LEFT JOIN object_type st ON s.object_type_id = st.id
    LEFT JOIN sampling_method cm ON s.collection_method_id = cm.collection_method_id
    LEFT JOIN platform p ON s.platform_id = p.id
    LEFT JOIN launch_platform lp ON s.launch_platform_id = lp.id
    LEFT JOIN initiative cfi ON s.cruise_field_prgrm_id = cfi.id
    LEFT JOIN geologic_time_scale gay ON s.geologic_age_younger_id = gay.geologic_time_id
    LEFT JOIN geologic_time_scale gao ON s.geologic_age_older_id = gao.geologic_time_id
    LEFT JOIN sesar_user cr ON s.cur_registrant_id = cr.sesar_user_id
    LEFT JOIN sesar_user co ON s.cur_owner_id = co.sesar_user_id
    LEFT JOIN country cty ON s.country_id = cty.id
    LEFT JOIN continent cnt on cty.continent_id = cnt.id
GROUP BY s.sample_id, cm.label, p.label, lp.label, cfi.label, cty.label, cnt.label, gmt.label,
		gmt.material_type_uri,gmt.scheme_uri, lc.label,  lc.material_type_uri, lc.scheme_uri,
		gay.label,gay.geologic_time_interval_uri,gay.scheme_uri, gao.label,
		gao.geologic_time_interval_uri,gao.scheme_uri, co.individual_id,cr.individual_id

limit 10

/*WHERE_CLAUSE_PLACEHOLDER*/