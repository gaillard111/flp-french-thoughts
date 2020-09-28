<?php
/**
 * Created by PhpStorm.
 * User: ars
 * Date: 21.11.18
 * Time: 17:24
 */

namespace ThoughtBundle\Entity;

use Doctrine\ORM\Mapping as ORM;
use Symfony\Component\Validator\Constraints as Assert;

/**
 * @ORM\Entity(repositoryClass="ThoughtBundle\Repository\TopicRepository")
 * @ORM\Table(name="topics")
 */
class Topic
{
    /**
     * @ORM\Id
     * @ORM\Column(type="integer")
     * @ORM\GeneratedValue(strategy="AUTO")
     */
    protected $id;

    /**
     * @Assert\NotBlank
     * @Assert\Length(max=256)
     * @ORM\Column(name="name", type="string")
     */
    protected $name;

    /**
     * @ORM\ManyToOne(targetEntity="Application\Sonata\UserBundle\Entity\User", inversedBy="topics")
     * @ORM\JoinColumn(name="user_id", referencedColumnName="id")
     */
    protected $user;

    /**
     * @ORM\OneToMany(targetEntity="ThoughtBundle\Entity\Chain", mappedBy="topic")
     */
    protected $chains;

    /**
     * @return mixed
     */
    public function getUser()
    {
        return $this->user;
    }

    /**
     * @param mixed $user
     *
     * @return Topic
     */
    public function setUser($user)
    {
        $this->user = $user;
        return $this;
    }

    /**
     * @return mixed
     */
    public function getId()
    {
        return $this->id;
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
     *
     * @return Topic
     */
    public function setName($name)
    {
        $this->name = $name;
        return $this;
    }

    /**
     * @return Chain
     */
    public function getChains()
    {
        return $this->chains;
    }

    /**
     * @param mixed $chains
     *
     * @return Topic
     */
    public function setChains($chains)
    {
        $this->chains = $chains;
        return $this;
    }
}