<?php

namespace ThoughtBundle\Entity;

use Doctrine\ORM\Mapping as ORM;

/**
 * Class Author
 *
 * @ORM\Entity(repositoryClass="ThoughtBundle\Repository\AuthorRepository")
 * @ORM\Table(name="author")
 * @ORM\HasLifecycleCallbacks()
 */
class Author
{
    /**
     * @ORM\Id
     * @ORM\Column(type="integer")
     * @ORM\GeneratedValue(strategy="AUTO")
     */
    protected $id;

    /**
     * @ORM\Column(name="name", type="string")
     */
    protected $name;

    /**
     * @ORM\Column(name="birth_date", type="string", nullable=true)
     */
    protected $birthDate;

    /**
     * @ORM\Column(name="sex", type="string", nullable=true)
     */
    protected $sex;

    /**
     * @ORM\Column(name="country", type="string", nullable=true)
     */
    protected $country;

    /**
     * @ORM\Column(name="continent", type="string", nullable=true)
     */
    protected $continent;

    /**
     * @ORM\Column(name="job", type="string", nullable=true)
     */
    protected $job;

    /**
     * @return mixed
     */
    public function getId()
    {
        return $this->id;
    }

    /**
     * @param mixed $id
     */
    public function setId($id)
    {
        $this->id = $id;
    }

    /**
     * @return mixed
     */
    public function getName()
    {
        return $this->name;
    }

    /**
     * @param mixed $name
     */
    public function setName($name)
    {
        $this->name = $name;
    }

    /**
     * @return mixed
     */
    public function getBirthDate()
    {
        return $this->birthDate;
    }

    /**
     * @param mixed $birthDate
     */
    public function setBirthDate($birthDate)
    {
        $this->birthDate = $birthDate;
    }

    /**
     * @return mixed
     */
    public function getSex()
    {
        return $this->sex;
    }

    /**
     * @param mixed $sex
     */
    public function setSex($sex)
    {
        $this->sex = $sex;
    }

    /**
     * @return mixed
     */
    public function getCountry()
    {
        return $this->country;
    }

    /**
     * @param mixed $country
     */
    public function setCountry($country)
    {
        $this->country = $country;
    }

    /**
     * @return mixed
     */
    public function getContinent()
    {
        return $this->continent;
    }

    /**
     * @param mixed $continent
     */
    public function setContinent($continent)
    {
        $this->continent = $continent;
    }

    /**
     * @return mixed
     */
    public function getJob()
    {
        return $this->job;
    }

    /**
     * @param mixed $job
     */
    public function setJob($job)
    {
        $this->job = $job;
    }
}
