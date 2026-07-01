/*ALTER TABLE teams
ADD COLUMN user_selection BOOLEAN DEFAULT FALSE;*/
/*UPDATE teams
SET user_selection = TRUE
WHERE name ILIKE '%vikings%'
 OR name ILIKE '%twins%'
 OR name ILIKE '%timberwolves%'
 OR name ILIKE '%wild'
 OR name ILIKE '%lynxs%'
 OR name ILIKE '%huskies%';*/

 SELECT * 
 FROM teams
 WHERE name ILIKE '%vikings%'
  OR name ILIKE '%twins%'
  OR name ILIKE '%timberwolves%'
  OR name ILIKE '%wild'
  OR name ILIKE '%lynxs%'
  OR name ILIKE '%huskies%'
  OR name ILIKE '%cardinal%';