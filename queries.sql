-- Requete avec filtre :
-- recupere uniquement les pays actifs
SELECT *
FROM countries
WHERE is_active = 1;


-- Requete utile a l'enrichissement :
-- recupere les informations des canaux actifs
SELECT
    channel_code,
    channel_name,
    channel_group
FROM channels
WHERE is_active = 1;