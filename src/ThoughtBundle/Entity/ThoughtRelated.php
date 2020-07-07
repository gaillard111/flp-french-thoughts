<?php

namespace ThoughtBundle\Entity;

use Doctrine\ORM\Mapping as ORM;

/**
 * @ORM\Entity()
 * @ORM\Table(name="thought_related")
 * @ORM\HasLifecycleCallbacks()
 */
class ThoughtRelated
{
    /**
     * @ORM\Id
     * @ORM\Column(type="integer")
     * @ORM\GeneratedValue(strategy="AUTO")
     */
    protected $id;

    /**
     * @ORM\ManyToOne(targetEntity="Application\Sonata\UserBundle\Entity\User", inversedBy="relatedThought")
     * @ORM\JoinColumn(name="owner_id", referencedColumnName="id", onDelete="CASCADE")
     */
    protected $owner;

    /**
     * @ORM\ManyToOne(targetEntity="ThoughtBundle\Entity\Thought", inversedBy="relatedThoughts")
     * @ORM\JoinColumn(name="thought_id", referencedColumnName="id")
     */
    protected $thought;

    /**
     * @ORM\ManyToOne(targetEntity="ThoughtBundle\Entity\Thought", inversedBy="inverseRelatedThoughts")
     * @ORM\JoinColumn(name="related_thoughts_id", referencedColumnName="id")
     */
    protected $relatedThought;


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
    public function getOwner()
    {
        return $this->owner;
    }

    /**
     * @param mixed $owner
     */
    public function setOwner($owner)
    {
        $this->owner = $owner;
    }

    /**
     * @return mixed
     */
    public function getThought()
    {
        return $this->thought;
    }

    /**
     * @param mixed $thought
     */
    public function setThought($thought)
    {
        $this->thought = $thought;
    }

    /**
     * @return mixed
     */
    public function getRelatedThought()
    {
        return $this->relatedThought;
    }

    /**
     * @param mixed $relatedThought
     */
    public function setRelatedThought($relatedThought)
    {
        $this->relatedThought = $relatedThought;
    }

}