<?php

namespace ThoughtBundle\Admin;

use Sonata\AdminBundle\Form\FormMapper;
use Sonata\AdminBundle\Datagrid\DatagridMapper;
use Sonata\AdminBundle\Datagrid\ListMapper;
use Sonata\AdminBundle\Show\ShowMapper;

/**
 * Class UserAdmin
 * @package ThoughtBundle\Admin
 */
class UserAdmin extends \Sonata\UserBundle\Admin\Entity\UserAdmin
{
    /**
     * @inheritdoc
     */
    public function getFormBuilder()
    {
        $this->formOptions['data_class'] = $this->getClass();

        $options = $this->formOptions;
        $options['validation_groups'] = (!$this->getSubject() || is_null($this->getSubject()->getId())) ? 'CustomRegistration' : 'CustomProfile';

        $formBuilder = $this->getFormContractor()->getFormBuilder($this->getUniqid(), $options);

        $this->defineFormBuilder($formBuilder);

        return $formBuilder;
    }

    /**
     * @param FormMapper $formMapper
     * @throws \Exception
     */
    protected function configureFormFields(FormMapper $formMapper)
    {
        // define group zoning
        $formMapper
            ->tab('User')
            ->with('Profile', ['class' => 'col-md-6'])->end()
            ->with('General', ['class' => 'col-md-6'])->end()
            ->end()
        ;

        $now = new \DateTime();

        $formMapper
            ->tab('User')
            ->with('General')
            ->add('email')
            ->add('plainPassword', 'text', [
                'required' => (!$this->getSubject() || is_null($this->getSubject()->getId())),
            ])
            ->end()
            ->with('Profile')
            ->add('firstname', null, ['required' => false])
            ->add('lastname', null, ['required' => false])
            ->add('roles', 'choice', [
                'choices' => [
                    'ROLE_ADMIN' => 'Admin',
                    'ROLE_MODERATOR' => 'Moderator',
                    'ROLE_USER' => 'User'
                ],
                'expanded' => false,
                'multiple' => true,
                'required' => false
            ])
            ->end()
            ->end()
        ;


    }

    /**
     * @param ListMapper $listMapper
     */
    protected function configureListFields(ListMapper $listMapper)
    {
        $listMapper
            ->addIdentifier('email')
            ->add('enabled', null, ['editable' => true])
            ->add('locked', null, ['editable' => true])
            ->add('createdAt')
        ;
    }

    /**
     * @param DatagridMapper $datagridMapper
     */
    protected function configureDatagridFilters(DatagridMapper $datagridMapper)
    {
        parent::configureDatagridFilters($datagridMapper);
    }
}
