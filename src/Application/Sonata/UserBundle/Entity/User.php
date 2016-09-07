<?php

/**
 * This file is part of the <name> project.
 *
 * (c) <yourname> <youremail>
 *
 * For the full copyright and license information, please view the LICENSE
 * file that was distributed with this source code.
 */

namespace Application\Sonata\UserBundle\Entity;

use Doctrine\ORM\Mapping as ORM;
use Sonata\UserBundle\Entity\BaseUser as BaseUser;

/**
 * @ORM\HasLifecycleCallbacks()
 */
class User extends BaseUser
{
    /**
     * @var int $id
     */
    protected $id;

    /**
     * @ORM\OneToMany(targetEntity="ThoughtBundle\Entity\Thought", mappedBy="owner")
     */
    protected $thoughts;

    /**
     * @ORM\OneToMany(targetEntity="ThoughtBundle\Entity\Chain", mappedBy="user")
     */
    protected $chains;

    /**
     * @ORM\OneToMany(targetEntity="ThoughtBundle\Entity\ChainComment", mappedBy="user")
     */
    protected $chainComments;

    /**
     * Get id
     *
     * @return int $id
     */
    public function getId()
    {
        return $this->id;
    }

    /**
     * Add thoughts
     *
     * @param \ThoughtBundle\Entity\Thought $thoughts
     * @return User
     */
    public function addThought(\ThoughtBundle\Entity\Thought $thoughts)
    {
        $this->thoughts[] = $thoughts;

        return $this;
    }

    /**
     * Remove thoughts
     *
     * @param \ThoughtBundle\Entity\Thought $thoughts
     */
    public function removeThought(\ThoughtBundle\Entity\Thought $thoughts)
    {
        $this->thoughts->removeElement($thoughts);
    }

    /**
     * Get thoughts
     *
     * @return \Doctrine\Common\Collections\Collection
     */
    public function getThoughts()
    {
        return $this->thoughts;
    }

    /**
     * @inheritdoc
     */
    public function prePersist()
    {
        parent::prePersist();
        $this->username = $this->email;
    }

    /**
     * @inheritdoc
     */
    public function preUpdate()
    {
        parent::preUpdate();
        $this->username = $this->email;
    }

    /**
     * Add chains
     *
     * @param \ThoughtBundle\Entity\Chain $chains
     * @return User
     */
    public function addChain(\ThoughtBundle\Entity\Chain $chains)
    {
        $this->chains[] = $chains;

        return $this;
    }

    /**
     * Remove chains
     *
     * @param \ThoughtBundle\Entity\Chain $chains
     */
    public function removeChain(\ThoughtBundle\Entity\Chain $chains)
    {
        $this->chains->removeElement($chains);
    }

    /**
     * Get chains
     *
     * @return \Doctrine\Common\Collections\Collection 
     */
    public function getChains()
    {
        return $this->chains;
    }

    /**
     * Add chainComments
     *
     * @param \ThoughtBundle\Entity\ChainComment $chainComments
     * @return User
     */
    public function addChainComment(\ThoughtBundle\Entity\ChainComment $chainComments)
    {
        $this->chainComments[] = $chainComments;

        return $this;
    }

    /**
     * Remove chainComments
     *
     * @param \ThoughtBundle\Entity\ChainComment $chainComments
     */
    public function removeChainComment(\ThoughtBundle\Entity\ChainComment $chainComments)
    {
        $this->chainComments->removeElement($chainComments);
    }

    /**
     * Get chainComments
     *
     * @return \Doctrine\Common\Collections\Collection 
     */
    public function getChainComments()
    {
        return $this->chainComments;
    }

    /**
     * Get fullName + email
     *
     * @return string
     */
    public function getFullNameEmail()
    {
        $fullName = trim(parent::getFullname());

        return  (!empty($fullName) ? $fullName . ', ' : '') . $this->getEmail();
    }
}
